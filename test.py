import win32gui,win32con,win32process
import psutil
win = win32gui.GetForegroundWindow()
print(win)
id=win32process.GetWindowThreadProcessId(win)
print(psutil.Process(id[1]))
dict= {
   '1':[1,2,3,4,5],
    '2':['wasd','qwe','asd','zxc','sdf'],
   "3": [213,123,321,213,123,]
}
l=dict['1']
l.append(6)
print(dict['1'])