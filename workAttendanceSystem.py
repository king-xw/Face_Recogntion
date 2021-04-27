import datetime
import time
import win32api
import win32con
import wx
import wx.grid
import sqlite3
from time import localtime, strftime
import os
from skimage import io as iio
import io
import zlib
import dlib  # 人脸识别的库dlib
import numpy as np  # 数据处理的库numpy
import cv2  # 图像处理的库OpenCv
import _thread
import threading
import win32com.client
import tkinter as tk
from tkinter import filedialog
import csv

spk = win32com.client.Dispatch("SAPI.SpVoice")

ID_NEW_REGISTER = 160
ID_FINISH_REGISTER = 161

ID_START_PUNCHCARD = 190
ID_END_PUNCARD = 191

ID_TODAY_LOGCAT = 283
ID_CUSTOM_LOGCAT = 284

ID_WORKING_HOURS = 301
ID_OFFWORK_HOURS = 302
ID_DELETE = 303

ID_WORKER_UNAVIABLE = -1

PATH_FACE = "data/face_img_database/"
# face recognition model, the object maps human faces into 128D vectors
facerec = dlib.face_recognition_model_v1("model/dlib_face_recognition_resnet_model_v1.dat")
# Dlib 预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')


def speak_info(info):
    spk.Speak(info)


def return_euclidean_distance(feature_1, feature_2):
    feature_1 = np.array(feature_1)
    feature_2 = np.array(feature_2)
    dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
    print("欧式距离: ", dist)
    if dist > 0.4:
        return "diff"
    else:
        return "same"


class WAS(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="智能监控打卡系统", size=(920, 560))

        self.Folderpath = None
        self.initMenu()
        self.initInfoText()
        self.initGallery()
        self.initDatabase()
        self.initData()

    def initData(self):
        self.name = ""
        self.id = ID_WORKER_UNAVIABLE
        self.face_feature = ""
        self.pic_num = 0
        self.flag_registed = False
        self.loadDataBase(1)

    def initMenu(self):

        menuBar = wx.MenuBar()  # 生成菜单栏
        menu_Font = wx.Font()  # Font(faceName="consolas",pointsize=20)
        menu_Font.SetPointSize(14)
        menu_Font.SetWeight(wx.BOLD)

        registerMenu = wx.Menu()  # 生成菜单
        self.new_register = wx.MenuItem(registerMenu, ID_NEW_REGISTER, "新建录入")
        self.new_register.SetBitmap(wx.Bitmap("drawable/new_register.png"))
        self.new_register.SetTextColour("SLATE BLACK")
        self.new_register.SetFont(menu_Font)
        registerMenu.Append(self.new_register)

        self.finish_register = wx.MenuItem(registerMenu, ID_FINISH_REGISTER, "完成录入")
        self.finish_register.SetBitmap(wx.Bitmap("drawable/finish_register.png"))
        self.finish_register.SetTextColour("SLATE BLACK")
        self.finish_register.SetFont(menu_Font)
        self.finish_register.Enable(False)
        registerMenu.Append(self.finish_register)

        puncardMenu = wx.Menu()
        self.start_punchcard = wx.MenuItem(puncardMenu, ID_START_PUNCHCARD, "开始签到")
        self.start_punchcard.SetBitmap(wx.Bitmap("drawable/start_punchcard.png"))
        self.start_punchcard.SetTextColour("SLATE BLACK")
        self.start_punchcard.SetFont(menu_Font)
        puncardMenu.Append(self.start_punchcard)

        self.end_puncard = wx.MenuItem(puncardMenu, ID_END_PUNCARD, "结束签到")
        self.end_puncard.SetBitmap(wx.Bitmap("drawable/end_puncard.png"))
        self.end_puncard.SetTextColour("SLATE BLACK")
        self.end_puncard.SetFont(menu_Font)
        self.end_puncard.Enable(False)
        puncardMenu.Append(self.end_puncard)

        logcatMenu = wx.Menu()
        self.today_logcat = wx.MenuItem(logcatMenu, ID_TODAY_LOGCAT, "输出今日日志")
        self.today_logcat.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.today_logcat.SetFont(menu_Font)
        self.today_logcat.SetTextColour("SLATE BLACK")
        logcatMenu.Append(self.today_logcat)

        self.custom_logcat = wx.MenuItem(logcatMenu, ID_CUSTOM_LOGCAT, "输出自定义日志")
        self.custom_logcat.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.custom_logcat.SetFont(menu_Font)
        self.custom_logcat.SetTextColour("SLATE BLACK")
        logcatMenu.Append(self.custom_logcat)

        setMenu = wx.Menu()
        self.working_hours = wx.MenuItem(setMenu, ID_WORKING_HOURS, "上班时间")
        self.working_hours.SetBitmap(wx.Bitmap("drawable/close_logcat.png"))
        self.working_hours.SetFont(menu_Font)
        self.working_hours.SetTextColour("SLATE BLACK")
        setMenu.Append(self.working_hours)

        self.offwork_hours = wx.MenuItem(setMenu, ID_OFFWORK_HOURS, "下班时间")
        self.offwork_hours.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.offwork_hours.SetFont(menu_Font)
        self.offwork_hours.SetTextColour("SLATE BLACK")
        setMenu.Append(self.offwork_hours)

        self.delete = wx.MenuItem(setMenu, ID_DELETE, "删除人员")
        self.delete.SetBitmap(wx.Bitmap("drawable/end_puncard.png"))
        self.delete.SetFont(menu_Font)
        self.delete.SetTextColour("SLATE BLACK")
        setMenu.Append(self.delete)

        menuBar.Append(registerMenu, "&人脸录入")
        menuBar.Append(puncardMenu, "&刷脸签到")
        menuBar.Append(logcatMenu, "&考勤日志")
        menuBar.Append(setMenu, "&设置")

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnNewRegisterClicked, id=ID_NEW_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnFinishRegisterClicked, id=ID_FINISH_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnStartPunchCardClicked, id=ID_START_PUNCHCARD)
        self.Bind(wx.EVT_MENU, self.OnEndPunchCardClicked, id=ID_END_PUNCARD)
        self.Bind(wx.EVT_MENU, self.ExportTodayLog, id=ID_TODAY_LOGCAT)
        self.Bind(wx.EVT_MENU, self.ExportCustomLog, id=ID_CUSTOM_LOGCAT)
        self.Bind(wx.EVT_MENU, self.SetWorkingHours, id=ID_WORKING_HOURS)
        self.Bind(wx.EVT_MENU, self.SetOffWorkHours, id=ID_OFFWORK_HOURS)
        self.Bind(wx.EVT_MENU, self.deleteBtn, id=ID_DELETE)

    def SetWorkingHours(self, event):
        global working
        global setWorkingSign
        setWorkingSign = False
        self.loadDataBase(1)
        # self.working_hours.Enable(True)
        self.working_hours = wx.GetTextFromUser(message="请输入上班时间", caption="温馨提示", default_value="08:00:00",
                                                parent=None)
        working = self.working_hours
        setWorkingSign = True
        pass

    def SetOffWorkHours(self, event):
        global offworking
        self.loadDataBase(1)
        # self.offwork_hours.Enable(True)
        self.offwork_hours = wx.GetTextFromUser(message="请输入下班时间", caption="温馨提示", default_value="18:00:00",
                                                parent=None)
        offworking = self.offwork_hours
        win32api.MessageBox(0, "请确保同时设置上班时间和下班时间并且先设置上班时间", "提醒", win32con.MB_ICONWARNING)
        if setWorkingSign:
            self.loadDataBase(4)
        else:
            win32api.MessageBox(0, "您未设置上班时间", "提醒", win32con.MB_ICONWARNING)
        pass

    def ExportTodayLog(self, event):
        global Folderpath1
        Folderpath1 = ""
        self.save_route1(event)
        if not Folderpath1 == "":
            self.loadDataBase(3)
            day = time.strftime("%Y-%m-%d")
            path = Folderpath1 + "/" + day + ".csv"
            f = open(path, 'w', newline='', encoding='utf-8')
            csv_writer = csv.writer(f)
            csv_writer.writerow(["编号", "姓名", "打卡时间", "是否迟到"])
            size = len(logcat_id)
            index = 0
            while size - 1 >= index:
                localtime1 = str(logcat_datetime[index]).replace('[', '').replace(']', '')
                csv_writer.writerow([logcat_id[index], logcat_name[index], localtime1, logcat_late[index]])
                index += 1;
            f.close()
        pass

    def ExportCustomLog(self, event):
        global dialog
        global t1
        global t2
        global Folderpath2
        Folderpath2 = ""
        dialog = wx.Dialog(self)
        Label1 = wx.StaticText(dialog, -1, "输入员工id", pos=(30, 10))
        t1 = wx.TextCtrl(dialog, -1, '', pos=(130, 10), size=(130, -1))
        Label2 = wx.StaticText(dialog, -1, "输出日期(天)", pos=(30, 50))
        sampleList = [u'1', u'3', u'7', u'30']
        t2 = wx.ComboBox(dialog, -1, value="1", pos=(130, 50), size=(130, -1), choices=sampleList,
                         style=wx.CB_READONLY)
        button = wx.Button(dialog, -1, "选择文件保存路径", pos=(120, 90))
        button.Bind(wx.EVT_BUTTON, self.save_route2, button)
        btn_confirm = wx.Button(dialog, 1, "确认", pos=(30, 150))
        btn_close = wx.Button(dialog, 2, "取消", pos=(250, 150))
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose, btn_close)
        btn_confirm.Bind(wx.EVT_BUTTON, self.DoCustomLog, btn_confirm)
        dialog.ShowModal()
        pass

    # 关闭主窗口前确认一下是否真的关闭
    def OnClose(self, event):
        dlg = wx.MessageDialog(None, u'确定要关闭本窗口吗?', u'操作提示', wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            dialog.Destroy()

    def OnClose1(self, event):
        dlg = wx.MessageDialog(None, u'确定要关闭本窗口吗?', u'操作提示', wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            dialog1.Destroy()

    def OnYes(self, event):
        dlg = wx.MessageDialog(None, u'确定要删除该编号的员工?', u'操作提示', wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            return True

    def deleteBtn(self, event):
        global dialog1
        global t4
        dialog1 = wx.Dialog(self)
        Label1 = wx.StaticText(dialog1, -1, "输入员工id: ", pos=(40, 34))
        t4 = wx.TextCtrl(dialog1, -1, '', pos=(130, 30), size=(130, -1))
        btn_confirm = wx.Button(dialog1, 1, "确认", pos=(30, 150))
        btn_close = wx.Button(dialog1, 2, "取消", pos=(250, 150))
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose1, btn_close)
        btn_confirm.Bind(wx.EVT_BUTTON, self.deleteById, btn_confirm)
        dialog1.ShowModal()

    def DoCustomLog(self, event):
        if not Folderpath2 == "":
            number = t1.GetValue()
            days = t2.GetValue()
            flag = self.findById(number, days)
            print("查询的天数是：", days)
            if flag:
                row = len(find_id)
                path = Folderpath2 + '/' + find_name[0] + '.csv'
                f = open(path, 'w', newline='', encoding='utf-8')
                csv_writer = csv.writer(f)
                csv_writer.writerow(["编号", "姓名", "打卡时间", "是否迟到"])
                for index in range(row):
                    s1 = str(find_datetime[index]).replace('[', '').replace(']', '')
                    csv_writer.writerow([str(find_id[index]), str(find_name[index]), s1, str(find_late[index])])

                f.close()
                success = wx.MessageDialog(None, '日志保存成功，请注意查看', 'info', wx.OK)
                success.ShowModal()
            else:
                warn = wx.MessageDialog(None, '输入id不正确，请重新输入', 'info', wx.OK)
                warn.ShowModal()
            dialog.Destroy()
        else:
            win32api.MessageBox(0, "请输入文件导出位置", "提醒", win32con.MB_ICONWARNING)

        pass

    def deleteById(self, event):
        global delete_name
        delete_name = []
        id = t4.GetValue()
        print("删除员工的id为:", id)
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        sql = 'select name from worker_info where id=' + id
        sql1 = 'delete from worker_info where id=' + id
        sql2 = 'delete from logcat where id=' + id
        length = len(cur.execute(sql).fetchall())
        if length <= 0:
            win32api.MessageBox(0, "没有查询到该员工，请重新输入ID", "提醒", win32con.MB_ICONWARNING)
            return False
        else:
            origin = cur.execute(sql).fetchall()
            for row in origin:
                delete_name.append(row[0])
                name = delete_name[0]
                print("名字是", name)
            if self.OnYes(event):
                cur.execute(sql1)
                cur.execute(sql2)
                conn.commit()
                dir = PATH_FACE + name
                for file in os.listdir(dir):
                    os.remove(dir + "/" + file)
                    print("已删除已录入人脸的图片", dir + "/" + file)
                os.rmdir(PATH_FACE + name)
                print("已删除已录入人脸的姓名文件夹", dir)
                dialog1.Destroy()
                self.initData()
                return True

    def findById(self, id, day):
        global find_id, find_name, find_datetime, find_late
        find_id = []
        find_name = []
        find_datetime = []
        find_late = []
        DayAgo = (datetime.datetime.now() - datetime.timedelta(days=int(day)))
        # 转换为其他字符串格式:
        day_before = DayAgo.strftime("%Y-%m-%d")
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        print(last_month.strftime("%Y-%m"))
        print(last_month)
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        sql = 'select id ,name,datetime,late from logcat where id=' + id

        if day == '30':
            str = "'"
            sql1 = 'select id ,name,datetime,late from logcat where id=' + id + ' ' + 'and datetime like ' + str + '%' + last_month.strftime(
                "%Y-%m") + '%' + str
        else:
            sql1 = 'select id ,name,datetime,late from logcat where id=' + id + ' ' + 'and datetime>=' + day_before
        length = len(cur.execute(sql).fetchall())
        if length <= 0:
            return False
        else:
            cur.execute(sql1)
            origin = cur.fetchall()
            for row in origin:
                find_id.append(row[0])
                find_name.append(row[1])
                find_datetime.append(row[2])
                find_late.append(row[3])
            return True
        pass

    def save_route1(self, event):
        global Folderpath1
        root = tk.Tk()
        root.withdraw()
        Folderpath1 = filedialog.askdirectory()  # 获得选择好的文件夹
        pass

    def save_route2(self, event):
        global Folderpath2
        root = tk.Tk()
        root.withdraw()
        Folderpath2 = filedialog.askdirectory()  # 获得选择好的文件夹
        pass

    def register_cap(self, event):
        # 创建 cv2 摄像头对象
        self.cap = cv2.VideoCapture(0)
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        while self.cap.isOpened():
            # cap.read()
            # 返回两个值：
            #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
            #    图像对象，图像的三维矩阵
            flag, im_rd = self.cap.read()

            # 每帧数据延时1ms，延时为0读取的是静态帧
            kk = cv2.waitKey(1)
            # 人脸数 dets
            dets = detector(im_rd, 1)

            # 检测到人脸
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    w = det.right() - det.left()
                    h = det.top() - det.bottom()
                    if w * h > maxArea:
                        biggest_face = det
                        maxArea = w * h
                        # 绘制矩形框

                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(), biggest_face.bottom()]),
                              (255, 0, 0), 2)
                img_height, img_width = im_rd.shape[:2]
                image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)

                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                shape = predictor(im_rd, biggest_face)
                features_cap = facerec.compute_face_descriptor(im_rd, shape)

                # 对于某张人脸，遍历所有存储的人脸特征
                for i, knew_face_feature in enumerate(self.knew_face_feature):
                    # 将某张人脸与存储的所有人脸数据进行比对
                    compare = return_euclidean_distance(features_cap, knew_face_feature)
                    if compare == "same":  # 找到了相似脸
                        self.infoText.AppendText(self.getDateAndTime() + "工号:" + str(self.knew_id[i])
                                                 + " 姓名:" + self.knew_name[i] + " 的人脸数据已存在\r\n")
                        self.flag_registed = True
                        self.OnFinishRegister()
                        _thread.exit()

                face_height = biggest_face.bottom() - biggest_face.top()
                face_width = biggest_face.right() - biggest_face.left()
                im_blank = np.zeros((face_height, face_width, 3), np.uint8)
                try:
                    for ii in range(face_height):
                        for jj in range(face_width):
                            im_blank[ii][jj] = im_rd[biggest_face.top() + ii][biggest_face.left() + jj]
                    if len(self.name) > 0:
                        cv2.imencode('.jpg', im_blank)[1].tofile(
                            PATH_FACE + self.name + "/img_face_" + str(self.pic_num) + ".jpg")  # 正确方法
                        self.pic_num += 1
                        print("写入本地：", str(PATH_FACE + self.name) + "/img_face_" + str(self.pic_num) + ".jpg")
                        self.infoText.AppendText(
                            self.getDateAndTime() + "图片:" + str(PATH_FACE + self.name) + "/img_face_" + str(
                                self.pic_num) + ".jpg保存成功\r\n")
                except:
                    print("保存照片异常,请对准摄像头")

                if self.new_register.IsEnabled():
                    _thread.exit()
                if self.pic_num == 30:
                    self.OnFinishRegister()
                    _thread.exit()

    def OnNewRegisterClicked(self, event):
        self.new_register.Enable(False)
        self.finish_register.Enable(True)
        self.loadDataBase(1)
        while self.id == ID_WORKER_UNAVIABLE:
            self.id = wx.GetNumberFromUser(message="请输入您的工号(-1不可用)",
                                           prompt="工号", caption="温馨提示",
                                           value=ID_WORKER_UNAVIABLE,
                                           parent=self.bmp, max=100000000, min=ID_WORKER_UNAVIABLE)
            for knew_id in self.knew_id:
                if knew_id == self.id:
                    self.id = ID_WORKER_UNAVIABLE
                    wx.MessageBox(message="工号已存在，请重新输入", caption="警告")

        while self.name == '':
            self.name = wx.GetTextFromUser(message="请输入您的的姓名,用于创建姓名文件夹",
                                           caption="温馨提示",
                                           default_value="", parent=self.bmp)

            # 监测是否重名
            for exsit_name in (os.listdir(PATH_FACE)):
                if self.name == exsit_name:
                    wx.MessageBox(message="姓名文件夹已存在，请重新输入", caption="警告")
                    self.name = ''
                    break
        os.makedirs(PATH_FACE + self.name)
        _thread.start_new_thread(self.register_cap, (event,))
        pass

    def OnFinishRegister(self):

        self.new_register.Enable(True)
        self.finish_register.Enable(False)
        self.cap.release()

        self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
        if self.flag_registed == True:
            dir = PATH_FACE + self.name
            for file in os.listdir(dir):
                os.remove(dir + "/" + file)
                print("已删除已录入人脸的图片", dir + "/" + file)
            os.rmdir(PATH_FACE + self.name)
            print("已删除已录入人脸的姓名文件夹", dir)
            self.initData()
            return
        if self.pic_num > 0:
            pics = os.listdir(PATH_FACE + self.name)
            feature_list = []
            feature_average = []
            for i in range(len(pics)):
                pic_path = PATH_FACE + self.name + "/" + pics[i]
                print("正在读的人脸图像：", pic_path)
                img = iio.imread(pic_path)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                dets = detector(img_gray, 1)
                if len(dets) != 0:
                    shape = predictor(img_gray, dets[0])
                    face_descriptor = facerec.compute_face_descriptor(img_gray, shape)
                    feature_list.append(face_descriptor)
                else:
                    face_descriptor = 0
                    print("未在照片中识别到人脸")
            if len(feature_list) > 0:
                for j in range(128):
                    # 防止越界
                    feature_average.append(0)
                    for i in range(len(feature_list)):
                        feature_average[j] += feature_list[i][j]
                    feature_average[j] = (feature_average[j]) / len(feature_list)
                self.insertARow([self.id, self.name, feature_average], 1)
                self.infoText.AppendText(self.getDateAndTime() + "工号:" + str(self.id)
                                         + " 姓名:" + self.name + " 的人脸数据已成功存入\r\n")
            pass

        else:
            os.rmdir(PATH_FACE + self.name)
            print("已删除空文件夹", PATH_FACE + self.name)
        self.initData()

    def OnFinishRegisterClicked(self, event):
        self.OnFinishRegister()
        pass

    def punchcard_cap(self, event):

        # 调用设置上班时间的函数，根据当前时间和上班时间判断是否迟到

        self.cap = cv2.VideoCapture(0)
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        self.loadDataBase(5)
        print("长度是")
        print(len(working_times))
        if len(working_times) == 0:
            win32api.MessageBox(0, "您未设置上班时间，请先设置上班时间后再设置下班时间", "提醒", win32con.MB_ICONWARNING)
            self.start_punchcard.Enable(True)
            self.end_puncard.Enable(False)
        else:
            working = working_times[0]
            print("-----------")
            print(working)
            offworking = offworking_times[0]
            print("-----------")
            print(offworking)
            while self.cap.isOpened():
                # cap.read()
                # 返回两个值：
                #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
                #    图像对象，图像的三维矩阵
                flag, im_rd = self.cap.read()
                # 每帧数据延时1ms，延时为0读取的是静态帧
                kk = cv2.waitKey(1)
                # 人脸数 dets
                dets = detector(im_rd, 1)

                # 检测到人脸
                if len(dets) != 0:
                    biggest_face = dets[0]
                    # 取占比最大的脸
                    maxArea = 0
                    for det in dets:
                        w = det.right() - det.left()
                        h = det.top() - det.bottom()
                        if w * h > maxArea:
                            biggest_face = det
                            maxArea = w * h
                            # 绘制矩形框

                    cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                                  tuple([biggest_face.right(), biggest_face.bottom()]),
                                  (255, 0, 255), 2)
                    img_height, img_width = im_rd.shape[:2]
                    image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                    pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                    # 显示图片在panel上
                    self.bmp.SetBitmap(pic)

                    # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                    shape = predictor(im_rd, biggest_face)
                    features_cap = facerec.compute_face_descriptor(im_rd, shape)

                    # 对于某张人脸，遍历所有存储的人脸特征
                    for i, knew_face_feature in enumerate(self.knew_face_feature):
                        # 将某张人脸与存储的所有人脸数据进行比对
                        compare = return_euclidean_distance(features_cap, knew_face_feature)
                        if compare == "same":  # 找到了相似脸
                            print("same")
                            flag = 0
                            nowdt = self.getDateAndTime()
                            for j, logcat_name in enumerate(self.logcat_name):
                                if logcat_name == self.knew_name[i] and nowdt[0:nowdt.index(" ")] == \
                                        self.logcat_datetime[
                                            j][
                                        0:self.logcat_datetime[
                                            j].index(" ")]:
                                    self.infoText.AppendText(nowdt + "工号:" + str(self.knew_id[i])
                                                             + " 姓名:" + self.knew_name[i] + " 签到失败,重复签到\r\n")
                                    speak_info(self.knew_name[i] + " 签到失败,重复签到 ")
                                    flag = 1
                                    break

                            if flag == 1:
                                break

                            if nowdt[nowdt.index(" ") + 1:-1] <= working:
                                self.infoText.AppendText(nowdt + "工号:" + str(self.knew_id[i])
                                                         + " 姓名:" + self.knew_name[i] + " 成功签到,且未迟到\r\n")
                                speak_info(self.knew_name[i] + " 成功签到 ")
                                self.insertARow([self.knew_id[i], self.knew_name[i], nowdt, "否"], 2)
                            elif offworking >= nowdt[nowdt.index(" ") + 1:-1] >= working:
                                self.infoText.AppendText(nowdt + "工号:" + str(self.knew_id[i])
                                                         + " 姓名:" + self.knew_name[i] + " 成功签到,但迟到了\r\n")
                                speak_info(self.knew_name[i] + " 成功签到,但迟到了 ")
                                self.insertARow([self.knew_id[i], self.knew_name[i], nowdt, "是"], 2)
                            elif nowdt[nowdt.index(" ") + 1:-1] > offworking:
                                self.infoText.AppendText(nowdt + "工号:" + str(self.knew_id[i])
                                                         + " 姓名:" + self.knew_name[i] + " 签到失败,超过签到时间\r\n")
                                speak_info(self.knew_name[i] + " 签到失败，超过下班时间 ")
                            self.loadDataBase(2)
                            break

                    if self.start_punchcard.IsEnabled():
                        self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
                        _thread.exit()

    def OnStartPunchCardClicked(self, event):
        self.start_punchcard.Enable(False)
        self.end_puncard.Enable(True)
        self.loadDataBase(2)
        threading.Thread(target=self.punchcard_cap, args=(event,)).start()
        pass

    def OnEndPunchCardClicked(self, event):
        self.start_punchcard.Enable(True)
        self.end_puncard.Enable(False)
        pass

    def initInfoText(self):
        # 少了这两句infoText背景颜色设置失败，莫名奇怪
        resultText = wx.StaticText(parent=self, pos=(10, 20), size=(90, 60))
        resultText.SetBackgroundColour(wx.GREEN)
        # resultText.SetBackgroundColour((12,12,12))
        self.info = "\r\n" + self.getDateAndTime() + "程序初始化成功\r\n"
        # 第二个参数水平混动条
        self.infoText = wx.TextCtrl(parent=self, size=(320, 500),
                                    style=(wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY))
        # 前景色，也就是字体颜色
        self.infoText.SetForegroundColour('Black')
        self.infoText.SetLabel(self.info)
        font = wx.Font()
        font.SetPointSize(12)
        font.SetWeight(wx.BOLD)
        font.SetUnderlined(True)

        self.infoText.SetFont(font)
        self.infoText.SetBackgroundColour('WHITE')
        pass

    def initGallery(self):
        self.pic_index = wx.Image("drawable/index.png", wx.BITMAP_TYPE_ANY).Scale(600, 500)
        self.bmp = wx.StaticBitmap(parent=self, pos=(320, 0), bitmap=wx.Bitmap(self.pic_index))
        pass

    def getDateAndTime(self):
        dateandtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
        return "[" + dateandtime + "]"

    # 数据库部分
    # 初始化数据库
    def initDatabase(self):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute('''create table if not exists worker_info
        (name text not null,
        id int not null primary key,
        face_feature array not null)''')
        cur.execute('''create table if not exists logcat
         (datetime text not null,
         id int not null,
         name text not null,
         late text not null)''')
        cur.execute('''create table if not exists time
         (id int
		constraint table_name_pk
			primary key,
         working_time time not null,
         offwork_time time not null)''')
        cur.close()
        conn.commit()
        conn.close()

    def adapt_array(self, arr):
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)

        dataa = out.read()
        # 压缩数据流
        return sqlite3.Binary(zlib.compress(dataa, zlib.Z_BEST_COMPRESSION))

    def convert_array(self, text):
        out = io.BytesIO(text)
        out.seek(0)

        dataa = out.read()
        # 解压缩数据流
        out = io.BytesIO(zlib.decompress(dataa))
        return np.load(out)

    def insertARow(self, Row, type):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        if type == 1:
            cur.execute("insert into worker_info (id,name,face_feature) values(?,?,?)",
                        (Row[0], Row[1], self.adapt_array(Row[2])))
            print("写人脸数据成功")
        if type == 2:
            cur.execute("insert into logcat (id,name,datetime,late) values(?,?,?,?)",
                        (Row[0], Row[1], Row[2], Row[3]))
            print("写日志成功")
            pass
        cur.close()
        conn.commit()
        conn.close()
        pass

    def loadDataBase(self, type):
        nowday = self.getDateAndTime()
        day = nowday[0:nowday.index(" ")]
        print(day)
        global logcat_id, logcat_name, logcat_datetime, logcat_late, working_times, offworking_times
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接

        cur = conn.cursor()  # 得到游标对象

        if type == 1:
            self.knew_id = []
            self.knew_name = []
            self.knew_face_feature = []
            cur.execute('select id,name,face_feature from worker_info')
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                self.knew_id.append(row[0])
                print(row[1])
                self.knew_name.append(row[1])
                print(self.convert_array(row[2]))
                self.knew_face_feature.append(self.convert_array(row[2]))
        if type == 2:
            self.logcat_id = []
            self.logcat_name = []
            self.logcat_datetime = []
            self.logcat_late = []
            cur.execute('select id,name,datetime,late from logcat')
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                self.logcat_id.append(row[0])
                print(row[1])
                self.logcat_name.append(row[1])
                print(row[2])
                self.logcat_datetime.append(row[2])
                print(row[3])
                self.logcat_late.append(row[3])
        if type == 3:
            logcat_id = []
            logcat_name = []
            logcat_datetime = []
            logcat_late = []
            s = "'"
            sql = 'select w.id,w.name,l.datetime,l.late from worker_info w left join logcat l  on  w.id=l.id and l.datetime like' + ' ' + s + day + '%' + s + ' ' + 'order by datetime desc'
            print(sql)
            cur.execute(sql)
            origin = cur.fetchall()
            for row in origin:
                print(row[0])
                logcat_id.append(row[0])
                print(row[1])
                logcat_name.append(row[1])
                print(row[2])
                logcat_datetime.append(row[2])
                print(row[3])
                logcat_late.append(row[3])
        if type == 4:
            sql = 'select working_time from time'
            cur.execute(sql)
            countResult = (cur.fetchall())
            print(countResult)
            str = "'"
            if not countResult:
                sql = 'insert into time (id,working_time,offworking_time) values (1,' + str + working + str + ',' + str + offworking + str + ')'
                cur.execute(sql)
                print(sql)
                conn.commit()
                print("插入时间成功")
            else:
                str="'"
                sql = 'update time set working_time=' + str + working + str + ',offworking_time=' + str + offworking + str + ' where id=1'
                cur.execute(sql)
                conn.commit()
                print(sql)
                print("更新时间成功")

        if type==5:
            sql = 'select working_time,offworking_time from time'
            cur.execute(sql)
            print(sql)
            origin = cur.fetchall()
            print(origin)
            working_times = []
            offworking_times = []
            for row in origin:
                print("这是数据库取出的上班时间")
                print(row[0])
                working_times.append(row[0])
                print("这是数据库取出的下班时间")
                print(row[1])
                offworking_times.append(row[1])
        cur.close()
        conn.commit()
        conn.close()
        pass


app = wx.App()
frame = WAS()
frame.Show()
app.MainLoop()
