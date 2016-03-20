import urllib
from time import sleep

class Jejemon():
    def translate(self, tr):
        data = urllib.urlencode({"translateme" : tr})
        # Now get that file-like object again, remembering to mention the data.
        f = urllib.urlopen(" http://kalokohan.guissmo.frih.net/translator.php", data)
        # Read the results back.
        s = f.read()
        
        start = str(s).rfind('<div class="shit">')+len(('<div class="shit">'))+1
        end = str(s).rfind('</div>')
        #print start, end
  
        f.close()
        return s[start:end]

jeje = Jejemon()

sleep(10)
print jeje.translate("hello julius")

