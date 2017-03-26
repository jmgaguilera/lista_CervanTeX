#!/usr/bin/env python3
# coding=utf-8

import xml.etree.ElementTree as ET
import codecs
import pycurl
import sys
import re
import itertools as IT
import io
from datetime import datetime
import locale
import sqlite3
from io import BytesIO
import re
import html


parser = ET.XMLParser()
parser.entity["nbsp"] = chr(160)
parser.entity["Aacute"] = chr(193)
parser.entity["acute"] = chr(180)
parser.entity["Atilde"] = chr(8764)
parser.entity["sup3"] = chr(179)
parser.entity["iexcl"] = chr(161)
parser.entity["shy"] = chr(173)
parser.entity["ntilde"] = chr(209)
parser.entity["copy"] = chr(169)

# descargar a mano el código fuente de la página que tiene el índice de los
# mensajes de la lista y guardarlo en un fichero.
# utilizar la shell para procesarlo
# Modificar esta variable con path al fichero
fich_a_cargar = "html_red_iris/pagina_raiz_febrero_2017.html"

f = codecs.open(fich_a_cargar, encoding='utf-8')
f_datos = f.read()
try:
    xml = ET.parse(fich_a_cargar,parser=parser)
except ET.ParseError as err:
    lineno, column = err.position
    err.msg = '{}\nlínea:{}\ncolumna:{}'.format(err, lineno, column)
    raise

xml = xml.getroot()


n="{http://www.w3.org/1999/xhtml}" # problema con los espacios sin nombre

#n = "{http://www.w3.org/TR/html4/loose.dtd}"
# buscar_temas = ".//%str[class='normalgroup']/%std[scope='row']/%sp/%sspan/%sa[@href]"
buscar_temas = ".//%str/%std/%sp/%sspan/%sa[@href]" % (n,n,n,n,n,)
temas = xml.findall(buscar_temas)

buscar_atrib = ".//%str/%std[@nowrap='nowrap']/%sp[@class='archive']" % (n,n,n,)
atrib = xml.findall(buscar_atrib)

red_iris_server = "https://listserv.rediris.es"

print("Número de artículos: ", len(temas)-1)

def limpiarTema(tema):
    temaf = tema
    temaff = temaf
    while True:
        temaff = temaff[len("re:"):] if temaff.lower().startswith("re:") else temaff
        temaff = temaff[len("fwd:"):] if temaff.lower().startswith("fwd:") else temaff
        if temaff == temaf:
            break
        else:
            temaf = temaff
    return temaff

def limpiarAutor(autor):
    if not autor is None:
        autorf = autor
    else:
        autorf = ""
    autorff = autorf
    while True:
        autorff = autorff[:len(autorff)-len(" <"):] if autorff.lower().endswith(" <") else autorff
        if autorff == autorf:
            break
        else:
            autorf = autorff
    return autorff

import pytz
zona_local_espanya = pytz.timezone('Europe/Madrid')

def convertir_fecha(fecha_entrada):
    """ La fecha viene en formato Fri, 17 Feb 2017 09:27:24 +0100
    """
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
    fecha_trabajo = datetime.strptime(fecha_entrada, '%a, %d %b %Y %H:%M:%S %z')
    #fecha_trabajo = fecha_trabajo.replace(tzinfo=pytz.UTC)
    normalizada = fecha_trabajo.astimezone(zona_local_espanya)
    fecha_salida = normalizada.strftime("%Y-%m-%d %H:%M:%S %z")
    return fecha_salida

def obtener_id_mensaje(temas, atrib, i):
    tema = temas[i].text
    tema = tema.replace("\n", " ")
    tema = limpiarTema(tema)
    if tema[0] == " ":
        tema = tema[1:]
    href = temas[i].get("href")
    autor = atrib[3*i].text
    autor = limpiarAutor(autor)
    fecha = atrib[3*i + 1].text
    fecha = convertir_fecha(fecha)
    lineas = atrib[3*i + 2].text
    return (href, tema, autor, fecha, lineas)

descargado = 0
def progress(download_t, download_d, upload_t, upload_d):
    global descargado
    if download_t > 0:
        d = int(download_d * 100 / download_t)+1
    else:
        d = 0
    if d > descargado:
        descargado = d
        sys.stdout.write("\rPorcentaje descargado: %d%%" % descargado)
        sys.stdout.flush()

def descargar_html(url):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.NOPROGRESS, 0)
    c.setopt(c.PROGRESSFUNCTION, progress)
    c.perform()
    c.close()
    return buffer

def encontrar_href_plain(texto):
    res = re.search(r'a href="(.*)">text/plain', texto)
    #print(res.group(1))
    return res.group(1)

def descargar(id_mensaje):
    buffer = descargar_html(red_iris_server+id_mensaje[0])
    body = buffer.getvalue()
    texto = body.decode("utf-8", "replace")
    #print(texto)
    res = re.search("<pre>(.*?)</pre>", texto, flags=re.MULTILINE|re.DOTALL)
    if res is None:
        url = encontrar_href_plain(texto)
        buffer = descargar_html(red_iris_server+url)
        body = buffer.getvalue()
        texto = body.decode("utf-8", "replace")
        res = re.search("<pre>(.*?)</pre>", texto, flags=re.MULTILINE|re.DOTALL)
        texto = html.unescape(res.group(1))
        #print(texto)
    else:
        texto = html.unescape(res.group(1))

    return texto


# main program
bd = sqlite3.connect("cervantex.db")
for i in range(len(temas)):
    id_mensaje = obtener_id_mensaje(temas, atrib, i)
    #print(id_mensaje)
    print("Descargando: ", i," de ", len(temas)-1)
    mensaje = descargar(id_mensaje)

    c = bd.cursor()
    print(id_mensaje[1])
    retorno = c.execute("insert into lista(tema, enlace, fecha, autor, descargado, lineas, mensaje) values(?,?,?,?,?,?,?)",
            ( id_mensaje[1], red_iris_server+id_mensaje[0], id_mensaje[3],
                id_mensaje[2], 1, id_mensaje[4], mensaje))
    bd.commit()


bd.close()


