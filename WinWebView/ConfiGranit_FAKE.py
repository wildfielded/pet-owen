#!/usr/bin/python3

''' !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Этот файл "ConfiGranit_FAKE.py" надо переименовать в "ConfiGranit.py"
    и переопределить переменные под рабочую конфигурацию.
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
''' Набор конфиговин, нужных для настройки работы программ
'''
DEFAULT_CFG = {
    'FILES': {
        'last_datafile': 'lastdata.txt',
        'last_cfgfile': 'lastcfg.txt',
        'json_file': 'history.json',
        'html_output': 'index.html',
        },
    'NETWORK': {
        'srv1_url': 'http://10.30.40.122/owen/',
        'srv2_url': 'http://10.30.40.123/owen/',
        },
    'SAMBA': {
        'login': 'WildDD',
        'passwd': 'password123',
        'domain': 'MYDOMAIN',
        'cli_name': 'testpc',
        'srv_name': 'CHECKPC',
        'srv_ip': '10.10.33.196',
        'srv_port': '445',
        'share_name': 'Owen$$',
        'data_path': 'owen.txt',
        'cfg_path': 'owen.cfg',
        },
    'PARAMETERS': {
        'tz_shift': '18000',
        'history_limit': '3600',
        },
    }

HTML_HEADER = '''<!DOCTYPE html>
<HTML LANG="ru">
<HEAD>
    <META CHARSET="utf-8">
    <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=utf-8">
    <META HTTP-EQUIV="Refresh" CONTENT="30">
    <META NAME="viewport" CONTENT="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <STYLE>
        body {
            font-family: Arial, sans-serif;
        }
        table,
        td,
        th {
            border-collapse: collapse;
            border-style: solid;
            border-width: 1px;
            padding: 0 10px 0 10px;
        }
        th {
            text-align: center;
        }
        td:nth-of-type(n+2) {
            text-align: center;
        }
        .green-state {
            background-color: #bbffbb;
        }
        .yellow-state {
            background-color: #ffff88;
            font-weight: 700;
        }
        .red-state {
            background-color: #ff0000;
            color: #ffffff;
            font-weight: 700;
        }
        .gray-state {
            background-color: #775533;
            color: #ffffff;
            font-weight: 700;
        }
        .black-state {
            background-color: #000000;
            color: #ffffff;
            font-weight: 700;
        }
    </STYLE>
    <TITLE>OWEN Temperatures</TITLE>
</HEAD>
<BODY>
    <HEADER></HEADER>
    <MAIN>
        <TABLE>
            <THEAD>
                <TR>
                    <TH>Помещение</TH>
                    <TH>T&nbsp;(&deg;C)</TH>
                    <TH>Max1<BR>(жёлтый)</TH>
                    <TH>Max2<BR>(красный)</TH>
                    <TH>Время<BR>измерения</TH>
                    <TH>История</TH>
                </TR>
            </THEAD>
            <TBODY>
'''

ROW_TEMPLATE = '''                <TR>
                    <TD>$place</TD>
                    <TD class="$state">$temp</TD>
                    <TD>$max1</TD>
                    <TD>$max2</TD>
                    <TD>$mtime</TD>
                    <TD><IMG SRC="$number.png" ALT="Датчик &numero;$number"></TD>
                </TR>
'''

DIAG_TEMPLATE = '''                <TR>
                    <TD COLSPAN="6" class="$state">
                        <SPAN>$place: $diag</SPAN>$alarmbutt
                    </TD>
                </TR>
'''

HTML_FOOTER = '''            </TBODY>
        </TABLE>
    </MAIN>
    <FOOTER></FOOTER>
</BODY>
</HTML>'''

#####=====----- THE END -----=====########################################