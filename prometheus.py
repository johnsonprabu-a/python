import os
import subprocess
import urllib.request
import wget
import hashlib
import tarfile
import sys
import pwd
import grp

#Requirements:
#python= above 3.6 "sudo add-apt-repository ppa:deadsnakes/ppa" "sudo apt update" "sudo apt install python3.6"
#pip3 "apt install python3-pip"
#"apt-get install python3-apt"
#
Target_URL = 'https://github.com/prometheus/prometheus/releases/download/v2.12.0/prometheus-2.12.0.linux-amd64.tar.gz'
SHA256SUM = 'b9f57b6e64fb3048742cfa7dbcc727e1df906d8020ef246a5e81b7959ae97e08'
Source_dir = '/opt/'
Dest_dir = '/opt/prometheus/'
Dest_file = '/opt/prometheus/prometheus.tar.gz'
Dest_efile = '/opt/prometheus/prometheus-2.12.0.linux-amd64/'
Config_dir = '/etc/prometheus'
Lib_dir = '/var/lib/prometheus/'
service_file = '/etc/systemd/system/prometheus.service'
service_dir = '/etc/systemd/system/'
BUF_SIZE = 65536
service_list = ["[Unit]", 'Description=Prometheus', 'Wants=network-online.target','After=network-online.target', '', '[Service]', 'User=prometheus', 'Group=prometheus', 'Type=simple', 'ExecStart=/usr/local/bin/prometheus --config.file /etc/prometheus/prometheus.yml --storage.tsdb.path /var/lib/prometheus/ --web.console.templates=/etc/prometheus/consoles --web.console.libraries=/etc/prometheus/console_libraries','','[Install]', 'WantedBy=multi-user.target']


def Create_Req_dirs():
    for i in Dest_dir, Config_dir, Lib_dir:
        if os.path.exists(i):
            print(f"{i} is already existing")
        else:
            print(f"Creating {i}")
            os.mkdir(i, mode=0o777)


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def Extract_Tarball():
    if Dest_file.endswith('tar.gz'):
        extr_file = tarfile.open(Dest_file, "r:gz")
        extr_file.extractall(Dest_dir)
        extr_file.close()
        print("Tarball extracted")
    else:
        print("File is not downloaded in tar.gz mode")
        sys.exit(status=False)


def add_prometheus_user():
    if not pwd.getpwnam('prometheus'):
        print("Adding Prometheus user")
        os.system("useradd --no-create-home --shell /bin/false prometheus")
    else:
        print("Prometheus user already exists")


def setting_file_permission():
    uid = pwd.getpwnam("prometheus").pw_uid
    gid = grp.getgrnam("prometheus").gr_gid
    # Moving respective files to It's directory
    os.chdir(Dest_efile)
    print(os.getcwd())
    if not os.path.exists('/etc/prometheus/consoles'):
        os.system("cp -rv consoles /etc/prometheus")
    if not os.path.exists('/etc/prometheus/consoles_libraries'):
        os.system("cp -rv console_libraries /etc/prometheus")
    if not os.path.isfile('/etc/prometheus/prometheus.yml'):
        os.system("cp -v prometheus.yml /etc/prometheus")
        subprocess.run(['chown', '-R', 'prometheus:prometheus', '/etc/prometheus/'])
    if not os.path.isfile('/usr/local/bin/prometheus'):
        subprocess.run(['cp', '-v', 'prometheus', '/usr/local/bin/'])
        subprocess.run(['chown', 'prometheus:prometheus', '/usr/local/bin/prometheus'])
    if not os.path.isfile('/usr/local/bin/promtool'):
        subprocess.run(['cp', '-v', 'promtool', '/usr/local/bin/'])
        subprocess.run(['chown', 'prometheus:prometheus', '/usr/local/bin/promtool'])
    # Setting FILE PERMISSION
    subprocess.run(['chown', '-R', 'prometheus:prometheus', '/etc/prometheus/'])


def setting_service_file():
    # Setting systemctl file
    f = open(service_dir + "prometheus.service", "w+")
    f = open(service_dir + "prometheus.service", "a+")
    for i in range(int(len(service_list))):
        f.write(service_list[i])
        f.write('\n')
    f.close()


def service_check(service):
    p = subprocess.Popen(["systemctl", "is-active", service], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output = output.decode('utf-8')
    return output


if os.getuid() is 0:
    print("Program is on Root User")
    Create_Req_dirs()
    print("Retrieving prometheus tarball on /opt")

    if not os.path.isfile(Dest_file):
        wget.download(Target_URL, Dest_dir + 'prometheus.tar.gz')
    else:
        sha_256 = sha256sum(Dest_file)
        print(sha_256)
        if sha_256 == SHA256SUM:
            print("Source Hash Verified")
            if not os.path.exists(Dest_efile):
                Extract_Tarball()
            else:
                print("Prometheus already extracted")

            add_prometheus_user()

            if pwd.getpwnam('prometheus'):
                setting_file_permission()

            if not os.path.isfile(service_file):
                setting_service_file()
            else:
                print("service file is already exists. Kindly check / do a cleanup")

            # Starting the service

            sstatus = service_check("prometheus")
            if sstatus is not 'inactive':
                print("Prometheus service is already running")
            else:
                subprocess.run(["systemctl" "start", "prometheus"])
                s_status = service_check("prometheus")
                if s_status is 'active':
                    print("Enabling service")
                    subprocess.run(["systemctl" "enable", "prometheus"])
                else:
                    print("There is some issue on the service level. Please check......!")
        else:
            print("Source Hash is wrong, please verify")
else:
    print("Run this program as Root User")
