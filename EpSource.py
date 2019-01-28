"""Module including classes and functions for EpSentinel"""


import sqlite3
import requests
import datetime
#from EpConf import *
from bs4 import BeautifulSoup
import re


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

    request_error = ""
    ep_number, ep_date = ep_number_ep_date
    se = str(ep_number // 100).zfill(2)
    ep = str(ep_number%100).zfill(2)

    # Import the search result page from piratebay
    url = tpb+"search/"+name+"%20s"+se+"e"+ep+"/0/7/0"
    print("Looking on TPB for episode: "+str(ep_number))

    try:
        page = requests.get(url)

    except Exception as e:  # Handling requests errors
        print("Error while connecting to TPB: " + repr(e))
        result_url = [(repr(e), "#")]
        for i in range(number_links - 1):
            result_url.append(("-", "#"))
        return result_url

    # Create the soup
    soup = BeautifulSoup(page.content, 'html.parser')

    # Find most seeded link
    links_exist = soup.select("div.detName")

    # Dump links found
    result_url = [(soup.select("div.detName")[i].select("a")[0].get_text(),
                   tpb+soup.select("div.detName")[i].select("a")[0].get("href"))
                  for i in range(min(len(links_exist), number_links))]
    # Add "Not found" links if necessary
    for i in range(number_links - len(links_exist)):
        result_url.append(("Not found","#"))

    return result_url


def new_show(name, missing_num):
    """Inserts new table with header for a new show"""

    # Format id of the table to alphanumeric char only
    pattern = re.compile('[\W]+')
    id = pattern.sub('', name)

    s = """
        <table id="{id}">
        <thead>
            <tr>
                <th colspan="4" class="left-text">{name} ({missing_num}) <span class="ui-icon ui-icon-caret-2-n-s expand"</th>
            </tr>
        </thead>
        <tbody hidden>""".format(id=id, name=name, missing_num=missing_num)

    return s


def insert(ep, href):
    """Insert in the page all the links given by href (look_tpb function output)"""

    s = """<tr><td class="left-text">{name_ep}</td>""".format(name_ep = ep)

    for link_name, link_href in href:
        s += """<td><a href={href} target="_blank">{ln}</a></td>""".format(href=link_href, ln=link_name)
    s += "</tr>"

    return s


def close_show():
    """Close properly the table for one show"""

    return "</tbody></table></br>"


def insert_next(next_ep):
    """Insert the next episode for a show in the Next episodes table"""

    s = """<tr>
                <td class="left-text">{name_show}</td>
                <td>{episode}</td>
                <td>{date}</td>
           </tr>""".format(name_show=next_ep[0], episode=str(next_ep[1]), date=str(next_ep[2]))

    return s


class TVShow:
    """Object representing a TVshow"""

    def __init__(self, idshow, name, thetvdbid):
        self.KodID = idshow
        self.name = name
        self.thetvdbID = thetvdbid

    def __repr__(self):
        return self.name+": KodID-"+str(self.KodID)+" TheTVdbID-"+self.thetvdbID

    def webscrap(self, token):
        """Gets all show episodes from thetvdb websites

        Returns tuple: ([(int EpisodeNumber e.g. 101, datetime.date(airdate))], (next episode number, next episode airdate))"""

        episodes = []
        date_pattern = '[0-9]{4}-[0-9]{2}-[0-9]{2}'
        last_page = 0
        page = 1

        # GET requests to scrap all episodes
        while last_page == 0:
            # Request for API page about the episode
            headers = {"Authorization": "Bearer {}".format(token), "Accept-Language": "en"}
            url = "https://api.thetvdb.com/series/{id}/episodes?page={page}".format(id=self.thetvdbID, page=page)
            r = requests.get(url, headers=headers)

            # Scrap all episodes of the page received
            for episode in r.json()['data']:
                # Get EpNumber
                epnum = episode["airedEpisodeNumber"]
                epseas = episode["airedSeason"]
                absnum = 100*epseas+epnum

                if epnum > 0 and epseas > 0 and re.match(date_pattern, episode["firstAired"]):
                    # Get EpDate
                    date_tab = episode["firstAired"].split("-")
                    airdate = datetime.date(int(date_tab[0]), int(date_tab[1]), int(date_tab[2]))

                    # Append Ep if already casted
                    #if airdate < datetime.date.today():
                    episodes.append((absnum, airdate))

            # Look if there is an other page
            if r.json()['links']['next'] is not None:
                page += 1
            else:
                last_page = 1

        # Sort episodes by date to determine when will be the next one
        episodes.sort(key=lambda tup: tup[1])

        # Divide b/w past and future episodes
        ep_pasts = [ep for ep in episodes if ep[1] < datetime.date.today()]
        ep_fut = [ep for ep in episodes if ep[1] > datetime.date.today()]

        if len(ep_fut) > 0:
            next_ep = ep_fut[0]
        else:
            next_ep = (0, 0)

        return ep_pasts, next_ep[0], next_ep[1]

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

    def missing_ep(self, db_file, web_eplist):
        """Check for missing episodes on local Kodi

        Returns list: [(int EpisodeNumber e.g. 101, datetime.date(airdate))]"""

        missing_ep = []
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
                          <meta charset="utf-8">
                          <meta name="viewport" content="width=device-width, initial-scale=1">
                          <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/smoothness/jquery-ui.css">
                          <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
                          <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
                          <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js"></script>
                          <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
                          <title>EpSentinel links sponsored by TPB</title>
                          
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
                        
                      </head>
                    
                      <body>
                        <div class="container-fluid">
                        <div class="row">
                        <div class="col-xs-8">
                    """)
        f.close()

    def open_table_next(self):
        """Closes the table col of missing episodes and opens the col for next episodes table"""

        f = open(self.path, 'a')
        f.write("""
        </div>
        <div class="col-xs-4">
        <table id="next_ep">
        <thead>
            <tr>
                <th>Coming episodes</th>
                <th>#</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>""")
        f.close()

    def dump_html(self, html):
        """Dump a complete html string in the html file"""

        f = open(self.path, 'a')
        f.write(html)
        f.close()


    def close(self):
        """Closes HTML tags to properly end HTML output file"""

        f = open(self.path, 'a')
        f.write(
                """
                </tbody>
                </div>
                </div>
                </div>
                
                <script type="text/javascript">
                    $(document).ready(function () {
                        $(".expand").click(function () {
                        var myid = $(this).closest('table').attr('id')
                           $('#'+myid+' tbody').toggle("slow");
                            });
                          });
                </script>
                
                </body></html>"""
                )
        f.close()

