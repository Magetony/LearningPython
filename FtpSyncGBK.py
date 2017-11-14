#coding=gbk

'''
    ftp自动下载、自动上传脚本，可以递归目录操作
'''

from ftplib import FTP
import os, sys, time
import socket


class SYNCFTP:
    def __init__(self, hostaddr, username, password, remotedir, port=21):
        self.hostaddr = hostaddr
        self.username = username
        self.password = password
        self.remotedir = remotedir
        self.port = port
        self.ftp = FTP()
        self.file_list = []

    def __del__(self):
        self.ftp.close()

    def login(self):
        ftp = self.ftp
        try:
            timeout = 60
            socket.setdefaulttimeout(timeout)
            ftp.set_pasv(True)
            print('开始连接到 %s' % (self.hostaddr))
            ftp.connect(self.hostaddr, self.port)
            print('成功连接到 %s' % (self.hostaddr))
            print('开始登录到 %s' % (self.hostaddr))
            ftp.login(self.username, self.password)
            print('成功登录到 %s' % (self.hostaddr))
            print(ftp.getwelcome())
        except Exception:
            deal_error("连接或登录失败")
        try:
            ftp.cwd(self.remotedir)
        except(Exception):
            deal_error('切换目录失败')

    def is_same_size(self, localfile, remotefile):
        try:
            remotefile_size = self.ftp.size(remotefile)
        except:
            remotefile_size = -1
        try:
            localfile_size = os.path.getsize(localfile)
        except:
            localfile_size = -1
        print('lo:%d  re:%d' % (localfile_size, remotefile_size), )
        if remotefile_size == localfile_size:
            return 1
        else:
            return 0

    def download_file(self, localfile, remotefile):
        if self.is_same_size(localfile, remotefile):
            print('%s 文件大小相同，无需下载' % localfile)
            return

        print('>>>>>>>>>>>>下载文件 %s ... ...' % localfile)
        file_handler = open(localfile, 'wb')
        self.ftp.retrbinary('RETR %s' % (remotefile), file_handler.write)
        file_handler.close()

    def download_files(self, localdir='./', remotedir='./'):
        try:
            self.ftp.cwd(remotedir)
        except:
            print('目录%s不存在，继续...' % remotedir)
            return
        if not os.path.isdir(localdir):
            os.makedirs(localdir)
        print('切换至目录 %s' % self.ftp.pwd())
        self.file_list = []
        self.ftp.dir(self.get_file_list)
        remotenames = self.file_list

        for item in remotenames:
            filetype = item[0]
            filename = item[1]
            local = os.path.join(localdir, filename)
            if filetype == 'd':
                self.download_files(local, filename)
            elif filetype == '-':
                self.download_file(local, filename)
        self.ftp.cwd('..')
        print('返回上层目录 %s' % self.ftp.pwd())

    def upload_file(self, localfile, remotefile):
        if not os.path.isfile(localfile):
            return
        if self.is_same_size(localfile, remotefile):
            print('跳过[相等]: %s' % localfile)
            return
        file_handler = open(localfile, 'rb')
        self.ftp.storbinary('STOR %s' % remotefile, file_handler)
        file_handler.close()
        print('已传送: %s' % localfile)

    def upload_files(self, localdir='./', remotedir='./'):
        if not os.path.isdir(localdir):
            return
        localnames = os.listdir(localdir)
        self.ftp.cwd(remotedir)
        for item in localnames:
            src = os.path.join(localdir, item)
            if os.path.isdir(src):
                try:
                    self.ftp.mkd(item)
                except:
                    print('目录已存在 %s' % item)
                self.upload_files(src, item)
            else:
                self.upload_file(src, item)
        self.ftp.cwd('..')

    def get_file_list(self, line):
        file_arr = self.get_filename(line)
        if file_arr[1] not in ['.', '..']:
            self.file_list.append(file_arr)

    def get_filename(self, line):
        pos = line.rfind(':')
        while (line[pos] != ' '):
            pos += 1
        while (line[pos] == ' '):
            pos += 1
        file_arr = [line[0], line[pos:]]
        return file_arr


def timenow():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


def deal_error(e):
    logstr = '%s 发生错误: %s\n' % (timenow(), e)
    print(logstr)
    file.write(logstr)
    sys.exit()


if __name__ == '__main__':
    file = open("log.txt", "a")
    logstr = timenow()
    # 配置如下变量
    hostaddr = '192.168.1.203'  # ftp地址
    username = 'bsfile'  # 用户名
    password = '111111'  # 密码
    port = 21  # 端口号
    rootdir_local = '.' + os.sep + 'bak/'  # 本地目录
    rootdir_remote = './'  # 远程目录

    f = SYNCFTP(hostaddr, username, password, rootdir_remote, port)
    f.login()

    # 先上传,后下载，遇到同名且文件大小不同的文件以本地为准
    f.upload_files(rootdir_local, rootdir_remote)
    f.download_files(rootdir_local, rootdir_remote)


    logstr += " ~ %s 同步完成\n" % timenow()
    print(logstr)

    file.write(logstr)
    file.close()
