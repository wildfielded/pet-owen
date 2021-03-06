#!/usr/bin/python3

from time import ctime, mktime, strptime, time
from configparser import ConfigParser, ExtendedInterpolation
import json
from string import Template

from smb.SMBConnection import SMBConnection
import png

import ConfiGranit as c_


#####=====----- Классы -----=====#####

class SensorDataBlock:
    ''' Создаёт объект данных одного датчика, задаёт стуктуру данных в виде
        словаря и методы их обработки
    '''
    def __init__(self):
        self.sensor_dict = {
            'sen_num': 0,
            'place': '',
            'warn_t': 0.0,
            'crit_t': 0.0,
            'measures': [{'timestamp': 0.0, 'value': 0.0, 'state': 'green-state'}]
            }

    def write_data(self, data_dict: dict={}):
        keys_ = data_dict.keys()
        if 'sen_num' in keys_:
            self.sensor_dict['sen_num'] = data_dict['sen_num']
        if 'place' in keys_:
            self.sensor_dict['place'] = data_dict['place']
        if 'warn_t' in keys_:
            self.sensor_dict['warn_t'] = data_dict['warn_t']
        if 'crit_t' in keys_:
            self.sensor_dict['crit_t'] = data_dict['crit_t']
        if 'state' in keys_:
            self.sensor_dict['measures'][0]['state'] = data_dict['state']
        if 'measures' in keys_:
            self.sensor_dict['measures'] = data_dict['measures'] + self.sensor_dict['measures']

    def read_data(self, keys_list: list=[]):
        output_dict = {}
        for key_ in keys_list:
            if key_ in self.sensor_dict.keys():
                output_dict[key_] = self.sensor_dict[key_]
        return output_dict


#####=====----- Функции -----=====#####

def get_current_files(cfg):
    ''' Забирает файл с последними измерениями и на всякий случай (если есть)
        текущий файл с пороговыми значениями с сервера OWEN и записывает себе
        локально.  Проверяет наличие и свежесть файла с измерениями (чтобы не
        старше двух минут), иначе возвращает соответственно строку
        "ERR_missing_data" или "ERR_rancid_data".
    '''
    last_datafile_ = cfg['FILES']['last_datafile']
    last_cfgfile_ = cfg['FILES']['last_cfgfile']
    login_ = cfg['SAMBA']['login']
    passwd_ = cfg['SAMBA']['passwd']
    domain_ = cfg['SAMBA']['domain']
    cli_name_ = cfg['SAMBA']['cli_name']
    srv_name_ = cfg['SAMBA']['srv_name']
    srv_ip_ = cfg['SAMBA']['srv_ip']
    srv_port_ = cfg.getint('SAMBA', 'srv_port')
    share_name_ = cfg['SAMBA']['share_name']
    data_path_ = cfg['SAMBA']['data_path']
    cfg_path_ = cfg['SAMBA']['cfg_path']

    with SMBConnection(login_, passwd_, cli_name_, srv_name_, domain_,
                       use_ntlm_v2=True, is_direct_tcp=True) as s_:
        s_.connect(srv_ip_, srv_port_)

        file_list_ = s_.listPath(share_name_, '/', pattern=data_path_)
        if file_list_:
            if file_list_[0].last_write_time > (time() - 120.0):
                with open(last_datafile_, 'wb') as f_:
                    s_.retrieveFile(share_name_, data_path_, f_)
                result_ = 'fresh_data'
            else:
                result_ = 'ERR_rancid_data'
        else:
            result_ = 'ERR_missing_data'

        if s_.listPath(share_name_, '/', pattern=cfg_path_):
            with open(last_cfgfile_, 'wb') as g_:
                s_.retrieveFile(share_name_, cfg_path_, g_)

        s_.close()
    return result_


def read_json(json_file):
    ''' Считывает файл с историческими данными в формате JSON и создаёт на
        их основе список экземпляров (объектов) класса SensorDataBlock
    '''
    output_obj_list = []
    try:
        with open(json_file, 'r', encoding='utf-8') as f_:
            history_list = json.load(f_)
        for dict_ in history_list:
            sensor_obj = SensorDataBlock()
            sensor_obj.write_data(dict_)
            output_obj_list.append(sensor_obj)
    except:
        pass
    return output_obj_list


def write_json(json_file, history_limit, input_obj_list):
    ''' Записывает в файл обновлённые исторические данные в формате JSON.
        Предварительно убирает устаревшие измерения, но так, чтобы их
        осталось минимум 2 для корректной обработки включения звуковых
        оповещений.
    '''
    output_obj_list = []
    for obj_ in input_obj_list:
        m_list_ = obj_.sensor_dict['measures']
        for m_ in m_list_[-1::-1]:
            if m_['timestamp'] < time() - history_limit:
                if len(m_list_) <= 2:
                    break
                m_list_.pop()
        output_obj_list.append(obj_.sensor_dict)
    with open(json_file, 'w', encoding='utf-8') as f_:
        json.dump(output_obj_list, f_, ensure_ascii=False, indent=2)


def parse_lastcfg(last_cfgfile, input_obj_list: list=[]):
    ''' Парсит данные из загруженного файла с пороговыми значениями по каждому
        датчику с некоторой валидацией данных и дополняет текущий (или создаёт
        новый) список экземпляров (объектов) класса SensorDataBlock
    '''
    try:
        with open(last_cfgfile, 'r', encoding='utf-8') as f_:
            cfg_list = f_.readlines()
    except UnicodeDecodeError:
        with open(last_cfgfile, 'r', encoding='cp1251') as f_:
            cfg_list = f_.readlines()
    output_obj_list = input_obj_list.copy()
    n_ = 0
    for line_ in cfg_list[1:]:
        n_ += 1
        list_ = line_.strip().split('\t')
        dict_ = {
            'sen_num': n_,
            'place': list_[0],
            'warn_t': float(list_[1]),
            'crit_t': float(list_[2])
            }
        if not input_obj_list:
            sensor_obj = SensorDataBlock()
            sensor_obj.write_data(dict_)
            output_obj_list.append(sensor_obj)
        else:
            output_obj_list[n_ - 1].write_data(dict_)
    return output_obj_list


def parse_lastdata(last_datafile, tz_shift, input_obj_list: list=[]):
    ''' Парсит данные из загруженного файла с измерениями по каждому датчику
        с некоторой валидацией данных, выставляет состояние в соответствии с
        пороговыми значениями и дополняет текущий (или создаёт новый) список
        экземпляров (объектов) класса SensorDataBlock
    '''
    try:
        with open(last_datafile, 'r', encoding='utf-8') as f_:
            data_list = f_.readlines()
    except UnicodeDecodeError:
        with open(last_datafile, 'r', encoding='cp1251') as f_:
            data_list = f_.readlines()
    output_obj_list = input_obj_list.copy()
    n_ = 0
    for line_ in data_list[1:]:
        n_ += 1
        list_ = line_.strip().split('\t')
        dict_ = {
            'sen_num': n_,
            'place': list_[2],
            }
        t_ = mktime(strptime(' '.join((list_[0], list_[1])), '%d.%m.%Y %H:%M:%S')) + tz_shift
        try:
            v_ = float(list_[3].replace(',', '.'))
        except:
            if list_[3].startswith('?'):
                v_ = '???'
                s_ = 'black-state'
            else:
                v_ = '!!!'
                s_ = 'gray-state'
        else:
            if v_ < output_obj_list[n_ - 1].sensor_dict['warn_t']:
                s_ = 'green-state'
            elif v_ < output_obj_list[n_ -1].sensor_dict['crit_t']:
                s_ = 'yellow-state'
            else:
                s_ = 'red-state'
        dict_['measures'] = [{'timestamp': t_, 'value': v_, 'state': s_}]
        if not input_obj_list:
            sensor_obj = SensorDataBlock()
            sensor_obj.write_data(dict_)
            output_obj_list.append(sensor_obj)
        else:
            output_obj_list[n_ - 1].write_data(dict_)
    return output_obj_list


def generate_html(input_obj_list: list=[], smb_result=''):
    ''' Принимает список объектов класса SensorDataBlock и заполняет
        соответствующими значениями по шаблонам табличные ячейки и итоговое
        состояние помещений, выводимое в одной или нескольких строках в конце
        таблицы.
    '''
    output_rows = ''
    output_diag = ''
    rows_ = Template(c_.ROW_TEMPLATE)
    diag_ = Template(c_.DIAG_TEMPLATE)
    if smb_result == 'fresh_data':
        for obj_ in input_obj_list:
            dict_ = obj_.sensor_dict
            n_ = str(dict_['sen_num'])
            p_ = dict_['place']
            t_ = str(dict_['measures'][0]['value']).replace('.', ',')
            y_ = int(dict_['warn_t'])
            r_ = int(dict_['crit_t'])
            s0_ = dict_['measures'][0]['state']
            try:
                s1_ = dict_['measures'][1]['state']
            except:
                s1_ = 'green-state'
            b_ = ''
            list_ = ctime(dict_['measures'][0]['timestamp']).split()
            m_ = '{} ({} {})'.format(list_[3], list_[2], list_[1])
            output_rows += rows_.safe_substitute(number=n_, place=p_, temp=t_,
                                                 max1=y_, max2=r_,
                                                 state=s0_, mtime=m_)
            if s0_ != 'green-state':
                if s0_ == 'yellow-state':
                    d_ = u'Подозрительное повышение температуры'
                elif s0_ == 'red-state':
                    d_ = u'Критическое повышение температуры'
                elif s0_ == 'black-state':
                    d_ = u'Нет показаний датчика больше минуты'
                elif s0_ == 'gray-state':
                    d_ = u'Неизвестная ошибка'
                else:
                    d_ = u'Неопределённая ошибка'
                if len(dict_['measures']) > 1 and s0_ != s1_:
                    b_ = u'\n                        <BUTTON ID="newalarm" STYLE="display: inline;">Выключить звук</BUTTON>'
                else:
                    b_ = ''
                output_diag += diag_.safe_substitute(state=s0_, place=p_,
                                                     diag=d_, alarmbutt=b_)
    elif smb_result == 'ERR_rancid_data':
        output_diag = diag_.safe_substitute(state='red-state',
                                            place=u'OWEN',
                                            diag=u'Данные не обновлялись больше двух минут.<BR>Программный сбой на сервере OWEN.',
                                            alarmbutt='')
    elif smb_result == 'ERR_missing_data':
        output_diag = diag_.safe_substitute(state='red-state',
                                            place=u'OWEN',
                                            diag=u'Файл с данными отсутствует на сервере OWEN.',
                                            alarmbutt='')
    if not output_diag:
        output_diag = diag_.safe_substitute(state='green-state',
                                            place=u'Все датчики',
                                            diag=u'Температура в норме',
                                            alarmbutt='')
    return output_rows + output_diag


def write_html(html_output, rows=''):
    ''' Записывает файл HTML. Использует заданные в модуле ConfiGranit шаблоны
        HTML-кода и Template для заполнения строк таблицы.
    '''
    with open(html_output, 'w', encoding='utf-8') as h_:
        h_.write(c_.HTML_HEADER + rows + c_.HTML_FOOTER)


def write_png(input_obj_list):
    ''' Продвинутый вариант создания графиков.
        Создаёт двумерную матрицу для создания PNG-файла по каждому датчику.
        Вертикальный размер картинки = 60px. Масштаб = 2px/градус. Уровень
        среднего значения - на высоте 20px. Сверху добавляется ещё 20px для
        наглядности - там могут появляться жёлтые и красные пороговые уровни
        температуры.
    '''
    for obj_ in input_obj_list:
        dict_ = obj_.read_data(['sen_num', 'warn_t', 'crit_t', 'measures'])
        m_list_ = []
        m_zero_ = 0
        m_sum_ = 0
        yelp_ = int(dict_['warn_t'] * 2)
        redp_ = int(dict_['crit_t'] * 2)
        for m_dict_ in dict_['measures']:
            try:
                if m_dict_['state'] == 'red-state':
                    colorbit_ = 3
                elif m_dict_['state'] == 'yellow-state':
                    colorbit_ = 2
                else:
                    colorbit_ = 1
                m_ = int(m_dict_['value'] * 2)
                m_list_.insert(0, (m_, colorbit_))
                m_sum_ += m_
            except:
                m_list_.insert(0, (0, 0))
                m_zero_ += 1
        try:
            average_t_ = int(m_sum_ / (len(m_list_) - m_zero_))
        except ZeroDivisionError:
            average_t_ = 20

        matrix_ = []
        for m_tup_ in m_list_:
            yel_delta_ = yelp_ - m_tup_[0]
            red_delta_ = redp_ - m_tup_[0]
            reduced_m_ = m_tup_[0] - average_t_ + 20
            list_ = [m_tup_[1] for y_ in range(reduced_m_)] + [0 for z_ in range(60 - reduced_m_)]
            list_len_ = len(list_)
            if reduced_m_ + yel_delta_ < list_len_ - 1:
                yel_pos_ = reduced_m_ + yel_delta_
                list_[yel_pos_] = 2
                list_[yel_pos_ + 1] = 2
            if reduced_m_ + red_delta_ < list_len_ - 1:
                red_pos_ = reduced_m_ + red_delta_
                list_[red_pos_] = 3
                list_[red_pos_ + 1] = 3
            matrix_.append(list_[:60:][::-1])
        transposed_matrix_ = [[matrix_[row_][col_] for row_ in range(len(matrix_))]
                                                   for col_ in range(len(matrix_[0]))]

        four_colors = [(224, 224, 224), (0, 160, 0), (255, 192, 0), (255, 64, 0)]
        png_file_ = str(dict_['sen_num']) + '.png'
        with open(png_file_, 'wb') as f_:
            p_ = png.Writer(len(transposed_matrix_[0]), len(transposed_matrix_),
                           palette=four_colors, bitdepth=2)
            p_.write(f_, transposed_matrix_)


#####=====----- Основной вызываемый код -----=====#####

def create(cfg_from_main: object=ConfigParser(interpolation=ExtendedInterpolation)):
    last_datafile_ = cfg_from_main['FILES']['last_datafile']
    last_cfgfile_ = cfg_from_main['FILES']['last_cfgfile']
    json_file_ = cfg_from_main['FILES']['json_file']
    html_output_ = cfg_from_main['FILES']['html_output']
    tz_shift_ = cfg_from_main.getfloat('PARAMETERS', 'tz_shift')
    history_limit_ = cfg_from_main.getfloat('PARAMETERS', 'history_limit')

    get_result = get_current_files(cfg_from_main)
    if get_result == 'fresh_data':
        current_obj_list = parse_lastdata(last_datafile_, tz_shift_, parse_lastcfg(last_cfgfile_, read_json(json_file_)))
        rows_ = generate_html(current_obj_list, smb_result=get_result)
        write_json(json_file_, history_limit_, current_obj_list)
        write_png(current_obj_list)
    else:
        rows_ = generate_html(smb_result=get_result)
    write_html(html_output_, rows=rows_)

#####=====----- THE END -----=====########################################