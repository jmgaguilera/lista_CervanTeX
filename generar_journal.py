#!/usr/bin/env python3
# coding=utf-8

import sqlite3

bd = sqlite3.connect("cervantex.db")

c = bd.cursor()

f = open("tex/201702_colección.tex", "w")

f.writelines(
        ['\\documentclass[a4paper,10pt]{article}\n',
         '\\usepackage{fontspec}\n',
         '\\usepackage{polyglossia}\n',
         '\\setdefaultlanguage{spanish}\n',
         '\\defaultfontfeatures{Ligatures={NoCommon}}\n',
         '\\setmainfont{TeX Gyre Pagella}[\n',
         ' SmallCapsFeatures={LetterSpace=4.0},\n',
         ' Numbers={OldStyle,Proportional}\n',
         ' ]\n',
         '\\setmonofont{TeX Gyre Heros}\n',
         '\\usepackage{listings}\n',
         '\\lstset{\n',
         '    basicstyle=\\small\\ttfamily,\n',
         '    columns=flexible,\n',
         '    breaklines=true\n',
         '}\n',
         '\\author{CervanTeX}\n',
         '\\title{Colección de mensajes de la lista de correo de CervanTeX}\n',
         '\\date{febrero de 2017\\\\ \\footnotesize{(mensajes en hora local de España)}}\n',
         '\\usepackage{nameref}\n',
         '\\setcounter{secnumdepth}{0}\n',
         '\\begin{document}\n',
         '\\maketitle\n\n',
         '\\tableofcontents\n\n'
        ])

temaant = ""

import re

def limpiar_mensaje(mensaje):
    blancos = 0
    mayorque = 0
    primero = True
    mens = ""
    for linea in mensaje.splitlines():
        if linea.strip() == "" and primero:
            continue
        if linea.strip() == "" and not primero:
            blancos += 1
            if blancos > 2:
                continue
        else:
            blancos = 0
        if len(linea) > 0 and linea[0] == ">":
            mayorque = mayorque + 1
            if mayorque == 5:
                mens += '> ...(texto omitido)...\n'
                continue
            else:
                if mayorque > 5:
                    continue
        else:
            mayorque = 0
        if re.match(r'^\-*$',linea.strip()) or \
           re.match("Normas para el correcto uso del correo electrónico:", linea) or \
           re.match(r".*?http\:\/\/www\.rediris\.es\/mail\/estilo\.html.*", linea):
            continue
        encuentro = re.search(r'(.*?)<a href="(.*?)".*?>(.*?)</a>(.*?)', linea,
                flags=re.MULTILINE | re.DOTALL)
        if encuentro is not None:
            linea = encuentro.group(1)+encuentro.group(2)+encuentro.group(4)
        encuentro = re.search(r'(.*?)</cgi-bin/wa\?LOGON(.*?)', linea)
        if encuentro is not None:
            linea = encuentro.group(1)
        encuentro = re.search(r'(.*?)/cgi-bin/wa\?LOGON(.*?)', linea)
        if encuentro is not None:
            linea = encuentro.group(1)
        encuentro = re.search(r'Archivos de ES-TEX: http://listserv.rediris.es/archives/es-tex.html', linea)
        if encuentro is not None:
            continue
        primero = False
        mens += linea+'\n'
    return mens

def limpiar_fecha(fecha):
    fecha = "Día "+fecha[8:len(fecha)-6]
    return fecha

for fila in c.execute("""select fechamin, fechamax, tema
                from (select min(fecha) as fechamin,
                             max(fecha) as fechamax,
                             tema
                      from lista group by tema)
                order by fechamin;"""):
    fechamin, fechamax, tema = fila
    print(fechamin)
    if temaant != tema:
        f.write('\\section{'+tema+'}\n')
    temaant = tema

    cc = bd.cursor()
    for fila2 in cc.execute("""select fecha, autor, mensaje
                               from lista
                               where tema = '%s'
                               order by fecha""" % tema):
        fecha, autor, mensaje = fila2
        fecha = limpiar_fecha(fecha)
        f.write('\n\\subsection{'+fecha+", "+autor+'}\n\n')
        f.write('\\begin{lstlisting}\n')
        mensaje = limpiar_mensaje(mensaje)
        f.write(mensaje+'\n')
        f.write('\\end{lstlisting}\n')

    cc.close()

f.write("\n\\end{document}\n")

f.close()
c.close()
