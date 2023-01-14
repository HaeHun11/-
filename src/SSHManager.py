import os
import paramiko
import logging
import time
import getpass


logging.basicConfig(level=logging.WARNING, filename="./ssh_error_log.txt", filemode="a",
                    format="=== %(asctime)s - %(message)s ===")  # this is log config method
# 로그위치 /var/log/ssh_log.log

DEBUG = True


class SSHManager(object):
    # class 공통 멤버변수 지양

    # type hint 이용
    def __init__(self, ip: str, port: int, username: str, password: str = "", use_ssh_key: bool = False, ssh_key_path: str = "") -> None:
        # 멤버변수 선언
        self.ip = ip  # ip address member variable(str)
        self.port = port  # port address member variable(int)
        self.username = username  # ID member variable(str)
        self.password = password  # password member variable(str)
        self.use_ssh_key = use_ssh_key
        if ssh_key_path:
            # localpath to id_rsa file member variable(str)
            self.ssh_key_path = ssh_key_path
        else:
            self.ssh_key_path = os.path.join(
                os.path.expanduser('~'), '.ssh/id_rsa')
        self.connected = False  # connection check member variable(bool)
        # session connection check member variable(bool)
        self.session_connected = False
        # paramiko ssh client member variable(paramiko.client.SSHClient)
        self.sshClient = paramiko.SSHClient()
        self.__connect()

    def __connect(self):  # ssh connect method(private)
        # ▼ If the server’s ip address is not found in either set of host keys, this method is used.
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.use_ssh_key:
            try:
                self.sshClient.connect(
                    self.ip, port=self.port, username=self.username, key_filename=self.ssh_key_path, timeout=1.5)
            except paramiko.ssh_exception.AuthenticationException:
                if DEBUG:
                    print("id, password can't correct!")
                # 스택 트레이스에 대한 로그 포함하여 ./ssh_error_log.txt 저장
                logging.exception("id, password can't correct!")
                self.connected = False
                return
            except Exception as e:
                if DEBUG:
                    print("exception %s: %s" % (e.__class__, e))
                logging.exception("%s" % (e))
                self.connected = False
                return
        else:
            try:
                self.sshClient.connect(
                    self.ip, port=self.port, username=self.username, password=self.password, timeout=1.5)
            except paramiko.ssh_exception.AuthenticationException:
                if DEBUG:
                    print("id, password can't correct!")
                # 스택 트레이스에 대한 로그 포함하여 ./ssh_error_log.txt 저장
                logging.exception("id, password can't correct!")
                self.connected = False
                return
            except Exception as e:
                if DEBUG:
                    print("exception %s: %s" % (e.__class__, e))
                logging.exception("%s" % (e))
                self.connected = False
                return
        self.connected = True

    def close(self):  # ssh client connect close method
        if self.session_connected:
            self.session_connected = False
            self.channel.close()
        if self.connected:
            self.connected = False
            self.sshClient.close()
            print("ssh client closed.")

    def command(self, command: str) -> None:  # command conduct method
        if self.connected:
            stdin, stdout, stderr = self.sshClient.exec_command(
                "%s" % (command))
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            if err:  # if error variable exist string, True
                print(err)
            else:
                print(out)
        else:
            print("ssh client isn't connected.")

    def session_open(self):  # session open method
        if self.session_connected != True:
            self.channel = self.sshClient.get_transport().open_session()  # create new channel
            self.channel.get_pty()
            self.channel.invoke_shell()
            self.channel.send("")
            outdata = errdata = ""
            time.sleep(1.0)
            while self.channel.recv_ready():
                outdata += str(self.channel.recv(1024).decode("utf-8"))
            while self.channel.recv_stderr_ready():
                errdata += str(self.channel.recv_stderr(1024).decode("utf-8"))
            if errdata:
                print(errdata)
            else:
                print(outdata)
                self.session_connected = True

    # session opend command conduct method
    def session_command(self, command: str) -> None:
        if self.session_connected:
            self.channel.send("%s\n" % (command))
            time.sleep(1.0)
            outdata = errdata = ""
            while self.channel.recv_ready():
                outdata += str(self.channel.recv(1024).decode("utf-8"))
            while self.channel.recv_stderr_ready():
                errdata += str(self.channel.recv_stderr(1024).decode("utf-8"))
            if errdata:
                print(errdata)
            else:
                print(outdata)
        else:
            print("session isn't opened.")

    def session_close(self):  # session close method
        if self.session_connected:
            self.session_connected = False
            self.channel.close()
        else:
            print("session isn't opened.")

    def upload(self, remotepath, localpath):  # upload method
        transport = paramiko.transport.Transport(
            self.ip, self.port)  # ssh Tunnel local variable
        if self.use_ssh_key:
            key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
            transport.connect(username=self.username, pkey=key)
        else:
            transport.connect(username=self.username, password=self.password)
        sftpClient = paramiko.SFTPClient.from_transport(transport)
        try:
            sftpClient.put(localpath, remotepath)
        except Exception as e:
            if DEBUG:
                print("exception %s - %s" % (e.__class__, e))
            logging.exception("%s" % (e))
        sftpClient.close()
        transport.close()

    def download(self, localpath, remotepath):  # download method
        transport = paramiko.transport.Transport(
            self.ip, self.port)  # ssh Tunnel local variable
        if self.use_ssh_key:
            key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
            transport.connect(username=self.username, pkey=key)
        else:
            transport.connect(username=self.username, password=self.password)
        sftpClient = paramiko.SFTPClient.from_transport(transport)
        try:
            sftpClient.get(remotepath, localpath)
        except Exception as e:
            if DEBUG:
                print("exception %s - %s" % (e.__class__, e))
            logging.exception("%s" % (e))
        sftpClient.close()
        transport.close()