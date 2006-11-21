#!/usr/bin/python

import sys, os, tempfile, socket

"""
ubuntu pkgs: festival festvox-rablpc16k (at least)

alsa plugin specs:
http://www.alsa-project.org/alsa-doc/alsa-lib/pcm_plugins.html
http://alsa.opensrc.org/index.php?page=.asoundrc
http://www.alsa-project.org/alsa-doc/doc-php/asoundrc.php

use mpg123 like this:
mpg123 -o alsa09 -a bathroom song.mp3

volumes are set at master=100, pcm=75

.asoundrc follows:
pcm.dshare {
    type dmix
    ipc_key 2048
    slave {
        pcm "hw:0"
        channels 2
    }
}
pcm.bathroom {
    type plug
    slave {
        pcm "dshare"
    }
    ttable.0.0 1
    ttable.1.0 1
}
pcm.frontdoor {
    type plug
    slave {
        pcm "dshare"
    }
    ttable.0.1 1
    ttable.1.1 1
}


"""

def say(sableXmlText, where="frontdoor"):
    """where is an alsa device name; see .asoundrc"""
    tf = tempfile.NamedTemporaryFile(suffix=".sable")
    tf.write("""<?xml version="1.0"?>
<!DOCTYPE SABLE PUBLIC "-//SABLE//DTD SABLE speech mark up//EN" 
	"Sable.v0_2.dtd"
[]>
<SABLE>""" + sableXmlText + """</SABLE>""")
    tf.flush()
    wav = tempfile.NamedTemporaryFile(suffix=".wav")
    text2wave = "text2wave"
    if socket.gethostname() == "xxdash":
        text2wave = "/my/dl/dl/festival/bin/text2wave"
    os.system("%s %s > %s" % (text2wave, tf.name, wav.name))
    os.system("aplay -D %s %s" % (where, wav.name))
    

if __name__ == '__main__':
    say(sys.argv[1])
    """
Without his penguin, <PITCH BASE="-20%"> which he left at home, </PITCH> he
       could not enter the restaurant.
       """
