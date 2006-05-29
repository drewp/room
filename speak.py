import os, tempfile, socket

"""
ubuntu pkgs: festival festvox-rablpc16k (at least)
"""

def say(sableXmlText):
    tf = tempfile.NamedTemporaryFile(suffix=".sable")
    tf.write("""<?xml version="1.0"?>
<!DOCTYPE SABLE PUBLIC "-//SABLE//DTD SABLE speech mark up//EN" 
	"Sable.v0_2.dtd"
[]>
<SABLE>""" + sableXmlText + """</SABLE>""")
    tf.flush()
    wav = tempfile.NamedTemporaryFile(suffix=".wav")
    text2wave = "text2wave"
    if socket.gethostname() == "dash":
        text2wave = "/my/dl/dl/festival/bin/text2wave"
    os.system("%s %s > %s" % (text2wave, tf.name, wav.name))
    os.system("play %s" % wav.name)
    

if __name__ == '__main__':
    say("""
Without his penguin, <PITCH BASE="-20%"> which he left at home, </PITCH> he
       could not enter the restaurant.
       """)
