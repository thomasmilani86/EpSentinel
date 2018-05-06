"""Module including classes and functions for EpSentinel"""


import sqlite3
import requests
import datetime
#from EpConf import *
from bs4 import BeautifulSoup


def get_tvseries(db_file):
    """Identify all the TV Series available in Kodi database

    Returns list: [object TVshow]"""

    serieslist = []

    # Connection to kodi video database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Query the list of series with name, idShow and thetvdbID
    query = """SELECT idShow, c00 as nameShow, c12 as thetvdb FROM tvshow"""
    c.execute(query)

    # Fetch the data retrieved
    data = c.fetchall()
    conn.close()

    for series in data:
        serieslist.append(TVShow(series[0], series[1], series[2]))

    return serieslist


def look_tpb(name, ep_number_ep_date, tpb, number_links):
    """Looks for the link to episode torrent on TPB
    Returns tuple: ([(str name, str link) * number_links], bool error_code)"""

    error = 0
    ep_number, ep_date = ep_number_ep_date
    se = str(ep_number // 100).zfill(2)
    ep = str(ep_number%100).zfill(2)

    # Import the search result page from piratebay
    url = tpb+"search/"+name+"%20s"+se+"e"+ep+"/0/7/0"
    print("Looking for episode: "+str(ep_number))
    page = requests.get(url)

    # Create the soup
    soup = BeautifulSoup(page.content, 'html.parser')

    # Find most seeded link
    links_exist = soup.select("div.detName")
    if len(links_exist) > 0:
        if len(links_exist) >= number_links:
            result_url = [(soup.select("div.detName")[i].select("a")[0].get_text(),
                           tpb+soup.select("div.detName")[i].select("a")[0].get("href")) for i in range(number_links)]
        else:
            result_url = [(soup.select("div.detName")[i].select("a")[0].get_text(),
                           tpb + soup.select("div.detName")[i].select("a")[0].get("href")) for i in range(len(links_exist))]
        print("Found! Thank you EpSentinel")

    else:
        result_url = ""
        error = 1
        print("Not found on TPB")

    print(result_url, error)

    return result_url, error


class TVShow:
    """Object representing a TVshow"""

    def __init__(self, idshow, name, thetvdbid):
        self.KodID = idshow
        self.name = name
        self.thetvdbID = thetvdbid

    def __repr__(self):
        return self.name+": KodID-"+str(self.KodID)+" TheTVdbID-"+self.thetvdbID

    def webscrap(self):
        """Gets all show episodes from thetvdb websites

        Returns list: [(int EpisodeNumber e.g. 101, datetime.date(airdate))]"""

        episodes = []

        # Import the page from theTVdb
        page = requests.get("https://www.thetvdb.com/index.php?id={}&lid=7&tab=seasonall&order=aired".format(self.thetvdbID))

        # Create the soup
        soup = BeautifulSoup(page.content, 'html.parser')
        listtable = soup.find(id="listtable").find_all('tr')
        del listtable[0]

        # Find latest aired episode
        for episode in listtable:

            tdlist = episode.find_all('td')

            # Re-format the episode number
            number = tdlist[0].get_text()
            date = tdlist[2].get_text()

            if number == 'Special':
                pass

            elif date == '':
                pass

            else:
                # Re-format the date
                date_tab = date.split("-")
                airdate = datetime.date(int(date_tab[0]), int(date_tab[1]), int(date_tab[2]))
                if airdate < datetime.date.today():
                    episodes.append((100*int(number.split()[0])+int(number.split()[2]), airdate))

        return episodes

    def localscrap(self, db_file):
        """Get all show episodes available on Kodi DB

        Returns list: [int EpisodeNumber e.g 101]"""

        # Connection to kodi video database
        conn = sqlite3.connect(db_file)
        c = conn.cursor()

        # Query the last episode info for each series
        query = """SELECT c12, c13 FROM episode WHERE idShow = {}""".format(self.KodID)
        c.execute(query)

        # Fetch the data retrieved
        data = c.fetchall()
        conn.close()

        # Put all the data in a table with standard format
        eplist = [int(episode[0])*100+int(episode[1]) for episode in data]

        return eplist

    def missing_ep(self, db_file):
        """Check for missing episodes on local Kodi

        Returns list: [(int EpisodeNumber e.g. 101, datetime.date(airdate))]"""

        missing_ep = []
        web_eplist = self.webscrap()
        local_eplist = self.localscrap(db_file)

        for ep in web_eplist:
            if ep[0] in local_eplist:
                pass
            else:
                missing_ep.append(ep)

        missing_ep = sorted(missing_ep, key=lambda epl: ep[0])

        return missing_ep


class HtmlSummary:
    """Class for html output file handling.

    Creates the file while initializing"""

    def __init__(self, out_path):
        self.path = out_path+"tpb_links.html"
        f = open(self.path, 'w')
        f.write("""<!DOCTYPE html>
                    <html lang="en" dir="ltr">
                      <head>
                        <style>
                          table {
                              font-family: arial, sans-serif;
                              border-collapse: collapse;
                              width: 100%;
                          }
                    
                          td, th {
                              border: 1px solid #dddddd;
                              text-align: center;
                              padding: 8px;
                          }
                    
                          .left-text{
                            text-align: left;
                          }
                    
                          tr:nth-child(even) {
                              background-color: #dddddd;
                          }
                        </style>
                        <meta charset="utf-8">
                        <title>EpSentinel links sponsored by TPB</title>
                      </head>
                    
                      <body>
                    """)
        f.close()

    def new_show(self, name):
        """Inserts new table with header for a new show"""

        f = open(self.path, 'a')
        s = """<table>
                <tr>
                    <th colspan="4" class="left-text">{}</th>
                </tr>""".format(name)

        f.write(s)
        f.close()

    def close_show(self):
        """Close properly the table for one show"""

        f = open(self.path, 'a')
        f.write("</table></br>")
        f.close()

    def insert(self, ep, href_error):
        """Insert in the page all the links given by href_error (look_tpb function output)"""

        f = open(self.path, 'a')

        s = """<tr>
                <td class="left-text">{name_ep}</td>""".format(name_ep = ep)
        f.write(s)

        if href_error[1] == 0:
            # At least one link has been found
            for link_name, link_href in href_error[0]:
                s = """<td><a href={href} target="_blank">{ln}</a></td>""".format(href=link_href, ln=link_name)
                f.write(s)
            for i in range(3-len(href_error[0])):
                f.write("""<td>-</td>""")
        else:
            #No link has been found
            for i in range(3):
                f.write("""<td>-</td>""")
        f.close()

    def close(self):
        """Closes HTML tags to properly end HTML output file"""

        f = open(self.path, 'a')
        f.write("</body></html>")
        f.close()


#tvlist = get_tvseries(db_path)
#print(tvlist)
#web_eplist = tvlist[0].webscrap()
#print(web_eplist)
#local_eplist = tvlist[0].localscrap(db_path)
#print(local_eplist)
#missing_ep = tvlist[0].missing_ep(db_path)
#print(len(missing_ep))
