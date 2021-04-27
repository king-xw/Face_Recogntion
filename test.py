import csv
import datetime
import sqlite3
import time
# 1. 创建文件对象
# f = open('D:\\a.csv', 'w', newline='', encoding='utf-8')
#
# # 2. 基于文件对象构建 csv写入对象
# csv_writer = csv.writer(f)
#
# # 3. 构建列表头
# csv_writer.writerow(["工号", "姓名", "打卡时间"])
#
# # 4. 写入csv文件内容
# csv_writer.writerow(["1", 'king', '2021-03-10 09:13:43'])
# # csv_writer.writerow(["c", '20', '男'])
# # csv_writer.writerow(["w", '22', '女'])
#
# # 5. 关闭文件
# f.close()
# with open('D:\\a.csv', 'r', encoding='utf-8') as f:
#       reader = csv.reader(f)
#       print(type(reader))
#
#       for row in reader:
#          print(row)

# with open('D:\\a.csv', 'r', encoding='utf-8') as f:
#     reader = csv.reader(f)
#     result = list(reader)
#     print(result[0])

# i = datetime.datetime.now()
#
# print ("今日的日期：" + time.strftime("%Y-%m-%d"))
#
# i = time.strftime("%Y-%m-%d")
# day = i-7
# print(day)

# d = datetime.datetime.now()
# def day_get(d):
#     oneday = datetime.timedelta(days=1)
#     day = d - oneday
#     date_from = datetime.datetime(day.year, day.month, day.day, 0, 0, 0)
#     date_to = datetime.datetime(day.year, day.month, day.day, 23, 59, 59)
#     print('---'.join([str(date_from), str(date_to)]))
#
# da = day_get(d)
# print(da)
# threeDayAgo = (datetime.datetime.now() - datetime.timedelta(days = 30))
# #转换为时间戳:
# timeStamp = int(time.mktime(threeDayAgo.timetuple()))
# #转换为其他字符串格式:
# otherStyleTime = threeDayAgo.strftime("%Y-%m-%d")
#
#
# print(otherStyleTime)
# print('select * from logcat where id=+''+id+''+datetime>=+''+day+''+')
conn = sqlite3.connect("inspurer.db")  # 建立数据库连接

cur = conn.cursor()  # 得到游标对象
#
# knew_id = []
# knew_name = []
# knew_face_feature = []
t = cur.execute('select * from logcat where id=6')
print(len(t.fetchall()))
# origin = cur.fetchall()

# logcat_id = []
# logcat_name = []
# logcat_datetime = []
# logcat_late = []
# cur.execute('SELECT * FROM logcat WHERE TO_DAYS(NOW( ) ) - TO_DAYS( datetime) <= 1')
# origin = cur.fetchall()
# for row in origin:
#     print(row[0])
#     logcat_id.append(row[0])
#     print(row[1])
#     logcat_name.append(row[1])
#     print(row[2])
#     print(str(row[2]).replace('[',''))
#     logcat_datetime.append(row[2])
#     print(row[3])
#     logcat_late.append(row[3])
# s  =  "'"
# str = '['+'1'+','+'king'+','+'212'+','+'yes'+']'
# str = 'king' + str(1)
# print(str)
#
# str1 = '[' + str(1) + ',' + king + ',' + str(3) + ',' + ki + ']'
# print(str1)