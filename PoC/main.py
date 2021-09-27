#!/usr/bin/python3

import configowen as c_
from smb.SMBConnection import SMBConnection

def get_last_file(output_file, login, passwd, domain, client,
                  server, addr, port, share, path):
    ''' Забирает текущий файл с сервера OWEN и записывает себе локально
    '''
    with open(output_file, 'wb') as f_:
        with SMBConnection(login, passwd, client, server, domain,
                           use_ntlm_v2=True, is_direct_tcp=True) as s_:
            s_.connect(addr, port)
            s_.retrieveFile(share, path, f_)
            s_.close()

def write_html(input_file, output_file, header_file, footer_file):
    ''' Записывает демо-файл HTML для отдачи по HTTP. Пока использует
        записанные в файлы куски HTML-кода.
    '''
    with open(header_file, 'r', encoding='utf-8') as f_:
        header_str = f_.read()
    with open(footer_file, 'r', encoding='utf-8') as f_:
        footer_str = f_.read()
    with open(input_file, 'r', encoding='cp1251') as f_:
        lastdata_str = f_.read()
    with open(output_file, 'w', encoding='utf-8') as f_:
        f_.write(header_str + lastdata_str + footer_str)

if __name__ == '__main__':
    get_last_file(c_.LAST_DATAFILE, c_.LOGIN, c_.PASSWD, c_.DOMAIN,
                  c_.CLI_NAME, c_.SRV_NAME, c_.SRV_IP, c_.SRV_PORT,
                  c_.SHARE_NAME, c_.FILE_PATH)
    write_html(c_.LAST_DATAFILE, c_.HTML_SAMPLE, c_.HTML_HEADER, c_.HTML_FOOTER)

###########################################################################