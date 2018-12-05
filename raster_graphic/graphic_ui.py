import wx
import cv2
import numpy as np
import re
from raster_graphic.line_double_step import point2D

class MainWindow(wx.Frame):
    def __init__(self, title, size ):
        wx.Frame.__init__(self, parent=None, title=title, size=size)
        #设置窗口的大小，并且大小不可变
        self.SetMaxSize(size)
        self.SetMinSize(size)
        self.size = size


        self.img = np.ones(( int(self.size[1] * 0.82),int(self.size[0] * 0.68), 3), dtype=np.uint8) * 255
        self.__base__ = point2D(int(self.img.shape[1] / 2), int(self.img.shape[0] / 2))
        self.genrateCoordinate(color=(0, 0, 0))
        self.bitmap = self.getBitmapFromCVImage(self.img, (int(self.size[0] * 0.68), int(self.size[1] * 0.82)))




        #ui的主要字体
        self.font = wx.Font(12, wx.SCRIPT, wx.NORMAL, wx.BOLD, False)

        #设置界面的透明性
        self.SetTransparent(1000)

        #创建各个面板，ui分为三个面板，一个主面板，两个子面板，子面板分为左右子面板
        #左面板用于显示录像和开始、暂停录像
        #右面板用于显示识别的结果以及让用户决定识别是否正确，若错误则会显示文本框用于输入正确答案
        self.createPanels()

        #对各个面板进行初始化
        self.initMainPanel()
        self.initLefttPanel()
        self.initRightPanel()


    def getBitmapFromCVImage(self, image, dsize):
        '''
        将cv2的图像文件转换为wxpython下的位图
        :param image: 通过cv2获得的图像，为numpy.ndarray类型
        :param dsize:需要转换到的目标大小
        :return: 若image不是None，则返回转换的位图；否则返回None
        '''
        if image is None:
            return None

        image = cv2.resize(image,dsize=dsize, interpolation=cv2.INTER_LANCZOS4)
        h, w = image.shape[0:2]
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        bitmap = wx.Bitmap.FromBuffer(w, h, image)
        return bitmap

    def createPanels(self):
        '''
        对象初始化时创建面板
        :return: 无
        '''
        self.main_panel = wx.Panel(self, wx.ID_ANY, self.size)
        self.left_subpanel = wx.Panel(self.main_panel, wx.ID_ANY,
                                      size=(int(self.size[0]*0.68), int(self.size[1]*0.82)))
        self.right_subpanel = wx.Panel(self.main_panel, wx.ID_ANY,
                                       size=(int(self.size[0]*0.32), int(self.size[1]*0.82)))

    def initMainPanel(self):
        '''
        初始化主面板，在主面板上设置布局，以及向布局中添加左右两个子面板
        :return: 无
        '''
        main_hbox = wx.BoxSizer(wx.HORIZONTAL)
        main_hbox.Add(self.left_subpanel)
        main_hbox.Add(self.right_subpanel)
        self.main_panel.SetBackgroundColour('#777777')

        self.main_panel.SetSizer(main_hbox)

    def initLefttPanel(self):
        '''
        初始化左面板，并设置布局为垂直盒布局，并向卜布局中添加控件
        左面板中的控件有：
            static_bitmap：用于显示视频
        :return: 无
        '''
        #注意：self.img.shape[1]指的是图片的宽度，shape[0]是图片的高度
        #也就是说x对于shape[1]，y对于shape[0]
        #而对numpy数组的操作是先行后列



        #self.bitmap = self.getBitmapFromCVImage(self.img, (int(self.size[0] * 0.68), int(self.size[1] * 0.82)))
        static_bitmap = wx.StaticBitmap(parent=self.left_subpanel, id=wx.ID_ANY, bitmap=self.bitmap,
                                        size=self.left_subpanel.GetSize())

        left_vbox = wx.BoxSizer(wx.VERTICAL)
        left_vbox.Add(static_bitmap)


        self.left_subpanel.SetOwnBackgroundColour('#ffffff')
        self.left_subpanel.SetSizer(left_vbox)

    def initRightPanel(self):
        '''
        初始化右面板，设置面板为垂直盒布局，并向布局中添加控件
        右面板中的控件有：
            right_vbox_hbox：用于放置right_btn 和 wrong_btn按钮的水平盒布局
        :return: 无
        '''
        panel_size = self.right_subpanel.GetSize()

        #选择绘制图形的提示标签
        choice_label = wx.StaticText(self.right_subpanel, id=wx.ID_ANY, label="请选择要绘制的图形:",
                                     size=(int(panel_size[0]*0.75),20))
        choice_label.SetForegroundColour((0,0,0))
        choice_label.SetOwnFont(self.font)

        self.shape_items = ["直线", "圆", "矩形", "多边形","多边形填充","直线裁剪", "多边形裁剪"]
        shapechoice = wx.Choice(self.right_subpanel, size=(int(panel_size[0]*0.75),40), id=wx.ID_VIEW_LIST, choices=self.shape_items)


        #输入绘制参数输入的提示标签
        input_label = wx.StaticText(self.right_subpanel, id=wx.ID_ANY, label="请输入绘制图形的参数:",
                                     size=(int(panel_size[0] * 0.75), 20))
        input_label.SetForegroundColour((0, 0, 0))
        input_label.SetOwnFont(self.font)
        #绘制图形需要的参数输入框
        input = wx.TextCtrl(self.right_subpanel,id=wx.ID_EDIT,size=(int(panel_size[0]*0.75),100),
                            style=wx.TE_RICH2 | wx.TE_PROCESS_ENTER | wx.TE_MULTILINE)

        input.SetOwnFont(self.font)
        input.Bind(wx.EVT_TEXT_ENTER, self.draw)

        #绘制按钮
        draw_btn = wx.Button(self.right_subpanel, wx.ID_ANY, label='绘制', size=(50, 35))
        draw_btn.Bind(wx.EVT_BUTTON, self.draw)

        # 清除坐标系按钮
        clear_btn = wx.Button(self.right_subpanel, wx.ID_ANY, label='清除', size=(50, 35))
        clear_btn.Bind(wx.EVT_BUTTON, self.clearShapes)

        right_vbox = wx.BoxSizer(wx.VERTICAL)
        right_vbox_hbox = wx.BoxSizer(wx.HORIZONTAL)

        #选择绘制的图形
        right_vbox.Add((-1, 10))
        right_vbox.Add(choice_label, flag=wx.CENTER)
        right_vbox.Add(shapechoice, flag=wx.CENTER)
        right_vbox.Add((-1, 10))

        #输入绘制图形的参数
        right_vbox.Add(input_label, flag=wx.CENTER)
        right_vbox.Add(input, flag=wx.CENTER)
        right_vbox.Add((-1, 10))

        #点击清除图形
        right_vbox_hbox.Add(draw_btn, flag=wx.CENTER)
        right_vbox_hbox.Add((30, -1))
        right_vbox_hbox.Add(clear_btn, flag=wx.CENTER)
        right_vbox_hbox.Add((30, -1))

        right_vbox.Add(right_vbox_hbox, flag=wx.CENTER)

        self.right_subpanel.SetOwnBackgroundColour('#999999')
        self.right_subpanel.SetSizer(right_vbox)

    def transPos(self, pos):
        return (self.__base__._x+pos[0], self.__base__._y-pos[1])

    def readInput(self):
        input = self.right_subpanel.GetChildren()[3]
        params = input.GetValue()
        # 编译正则表达式，匹配整数
        pattern = re.compile('[-]?\d+')
        # 将用户的输入转换成数字
        params_list = [int(x) for x in pattern.findall(params)]
        return params_list

    def draw(self, e):
        params_list = self.readInput()
        if(params_list == []):
            return

        #获得当前被选中的形状
        if self.right_subpanel.GetChildren()[1].GetCurrentSelection() == wx.NOT_FOUND:
            return
        selected_idx = self.right_subpanel.GetChildren()[1].GetCurrentSelection()

        print(self.shape_items[selected_idx])

        print(params_list)
        if (len(params_list) == 4 and self.shape_items[selected_idx]=="直线"):
            #画直线
            pnt1 = (params_list[0], params_list[1])
            pnt2 = (params_list[2], params_list[3])
            self.drawLine(pnt1, pnt2)
        if (len(params_list) == 3 and self.shape_items[selected_idx] == "圆"):
            #画圆
            center = (params_list[0], params_list[1])
            radius = params_list[2]
            self.drawCircle(center, radius)

        if (len(params_list) == 4 and self.shape_items[selected_idx] == "矩形"):
            # 画矩形
            pnt1 = (params_list[0], params_list[1])
            pnt2 = (params_list[2], params_list[3])
            self.drawRect(pnt1, pnt2)
        if (len(params_list) >= 6 and self.shape_items[selected_idx] == "多边形"):
            #画多边形
            pnts = []
            for i in range(0, len(params_list), 2):
                pnts.append([params_list[i], params_list[i+1]])
            self.drawPoloy(pnts)
        if (len(params_list) >= 6 and self.shape_items[selected_idx] == "多边形填充"):
            # 填充多边形
            pnts = []
            for i in range(0, len(params_list), 2):
                pnts.append([params_list[i], params_list[i + 1]])
            self.fillPoloy(pnts)

        if (len(params_list) == 8 and  self.shape_items[selected_idx] == "直线裁剪"):
            x1,y1,x2,y2,win_x1,win_y1,win_x2,win_y2 = params_list
            self.drawRect((win_x1,win_y1),(win_x2,win_y2),(0,0,255))
            #获得窗口的左右上下边界
            XL = win_x1 if win_x1 < win_x2 else win_x2
            XR = win_x2 if win_x2 > win_x1 else win_x1
            YT = win_y1 if win_y1 > win_y2 else win_y2
            YB = win_y2 if win_y2 < win_y1 else win_y1
            print(x1,' ',y1,' ',x2,' ',y2,' ',XL,' ',YT,' ',XR,' ',YB)
            self.LB_LineClip(x1,y1,x2,y2,XL,XR,YB,YT)

        if (len(params_list) >= 10 and self.shape_items[selected_idx] == "多边形裁剪"):
            pnts = []
            for i in range(0, len(params_list), 2):
                if i < len(params_list)-4:
                    pnts.append((params_list[i], params_list[i+1]))
                else:
                    break
            win_x1, win_y1, win_x2, win_y2 = params_list[-4:]
            self.drawRect((win_x1, win_y1), (win_x2, win_y2), (0, 0, 255))
            # 获得窗口的左右上下边界
            XL = win_x1 if win_x1 < win_x2 else win_x2
            XR = win_x2 if win_x2 > win_x1 else win_x1
            YT = win_y1 if win_y1 > win_y2 else win_y2
            YB = win_y2 if win_y2 < win_y1 else win_y1
            self.poloyClip(pnts, XL, XR, YB, YT)


    def clip(self, p, q, utuple:'list'):
        r = 0.0
        if (p < 0.0):
            r = q / p
            if (r > utuple[1]):
                return False
            elif (r > utuple[0]):
                utuple[0] = r
        elif (p > 0.0) :
            r = q / p
            if (r < utuple[0]):
                return False
            elif (r < utuple[1]):
                utuple[1] = r
        elif (q < 0.0):
            return False
        return True

    def LB_LineClip(self,x1, y1, x2, y2, XL, XR, YB, YT,color=(255,0,0)):
        #140, 100, 10, 10, 10,10 70, 80
        utuple = [0.0, 1.0]
        dx = x2 - x1
        dy = y2 - y1
        if (self.clip(-dx, x1 - XL,utuple)):
            if (self.clip(dx, XR - x1, utuple)):
                if (self.clip(-dy, y1 - YB, utuple)):
                    if (self.clip(dy, YT - y1, utuple)):
                        if (utuple[1] < 1.0) :
                            x2 = int(x1 + utuple[1] * dx)
                            y2 = int(y1 + utuple[1] * dy)
                        if (utuple[0] > 0.0) :
                            x1 = int(x1 + utuple[0] * dx)
                            y1 = int(y1 + utuple[0] * dy)
                        #print('pnt1:',(x1,y1),'  pnt2:',(x2,y2))
                        self.drawLine((x1,y1), (x2,y2), color)
                        return((x1,y1),(x2,y2))
        return None

    def poloyClip(self, pnts, XL,XR,YB,YT):
        #0, 0, 80, 0, 40, 100, 0, 0, 70, 80
        pts = []
        for i in range(0,len(pnts)):
            if i < len(pnts)-1:
                x1,y1 = pnts[i]
                x2,y2 = pnts[i+1]
                tmp = self.LB_LineClip(x1,y1,x2,y2, XL, XR, YB, YT)
            else:
                x1, y1 = pnts[i]
                x2, y2 = pnts[0]
                tmp = self.LB_LineClip(x1,y1,x2,y2, XL, XR, YB, YT)
            if tmp != None:
                p1,p2 = tmp
                pts.append(p1)
                pts.append(p2)
        #print(pts)
        self.fillPoloy(pts)


    def drawLine(self,pnt1, pnt2, color=(0,0,0)):
        pnt1 = self.transPos(pnt1)
        pnt2 = self.transPos(pnt2)
        cv2.line(self.img, pnt1, pnt2, color=color)
        self.flashCoordinate()

    def drawCircle(self, center, radius, color=(0,0,0)):
        center = self.transPos(center)
        cv2.circle(self.img, center, radius, color)
        self.flashCoordinate()

    def drawRect(self, pnt1, pnt2, color=(0,0,0)):
        pnt1 = self.transPos(pnt1)
        pnt2 = self.transPos(pnt2)
        cv2.rectangle(self.img, pnt1, pnt2, color=color)
        self.flashCoordinate()

    def drawPoloy(self, pnts, color=(0,0,0)):
        for i in range(len(pnts)):
            x,y = self.transPos(pnts[i])
            pnts[i] = [x,y]
        pnts = np.array(pnts)
        pnts = pnts.reshape((-1,1,2))
        print(pnts)
        cv2.polylines(self.img, [pnts], isClosed=True, color=color)
        self.flashCoordinate()

    def fillPoloy(self, pnts, color=(0,255,0)):
        for i in range(len(pnts)):
            x,y = self.transPos(pnts[i])
            pnts[i] = [x,y]
        #dtype必须设置成np.int32不然画不成，奇怪！！！
        pnts = np.array([pnts], np.int32)
        cv2.fillPoly(self.img, pnts,color,cv2.LINE_AA)
        self.flashCoordinate()

    def __drawScale__(self,step,color=(0,0,255)):
        '''
        在图片上标记处坐标轴的间隔
        :param step: 每个间隔之间的距离
        :param color: 间隔的颜色
        :return:
        '''

        for x in range(self.__base__._x, self.img.shape[1], step):
            self.img[self.__base__._y-5:self.__base__._y, x ] = color
        for x in range(self.__base__._x, 0, -step):
            self.img[self.__base__._y - 5:self.__base__._y, x] = color
        for y in range(self.__base__._y, self.img.shape[0], step):
            self.img[y, self.__base__._x:self.__base__._x+5] = color
        for y in range(self.__base__._y, 0, -step):
            self.img[y, self.__base__._x:self.__base__._x+5] = color
        cv2.putText(self.img,'step--'+str(step),(self.img.shape[1]-58,10), cv2.FONT_HERSHEY_COMPLEX,0.3,color,1)
        cv2.putText(self.img, 'copyright@GZY', (self.img.shape[1]-95, 20), cv2.FONT_HERSHEY_COMPLEX, 0.35, color,1)
        x,y = self.__base__.__tuple__()
        cv2.putText(self.img, 'X', (self.img.shape[1]-30, y+10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, color, 1)
        cv2.putText(self.img, 'Y', (x+10, 0 + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, color, 1)
        x = x+10
        y = y+15
        cv2.putText(self.img, 'O', (x,y) , cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, color,2)


    def genrateCoordinate(self, color=(0,0,255)):
        '''
        在一副图片上生成二维坐标系，可以指定图片在屏幕坐标系下的某个位置为原点，并指定坐标系颜色
        :param color: 坐标轴的颜色
        :return:
        '''
        self.img[self.__base__._y, : ] = color
        self.img[ : , self.__base__._x] = color
        self.img[self.__base__._x, self.__base__._y] = color
        self.__drawScale__(10, color)

    def clearShapes(self, e):
        self.img = np.ones(( int(self.size[1] * 0.82),int(self.size[0] * 0.68), 3), dtype=np.uint8) * 255
        self.genrateCoordinate(color=(0, 0, 0))
        self.left_subpanel.GetChildren()[0].SetBitmap(self.bitmap)

    def flashCoordinate(self):
        bitmap = self.getBitmapFromCVImage(self.img, dsize=(int(self.size[0] * 0.68), int(self.size[1] * 0.82)))
        self.left_subpanel.GetChildren()[0].SetBitmap(bitmap)





def testUI(title, size):
    app = wx.App()
    win = MainWindow(title=title, size=size)
    win.Show()
    app.MainLoop()

def main():
    testUI('光栅图形学', (1000, 650))


if __name__ == '__main__':
    main()