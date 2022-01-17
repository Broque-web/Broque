from bs4 import BeautifulSoup
import requests


flag = True
fore_bet = "https://www.forebet.com/en/football-tips-and-predictions-for-today"
try:
    fore_bet_html = requests.get(fore_bet).text
    soup = BeautifulSoup(fore_bet_html, "html.parser")
    elements = soup.find_all("div", class_="rcnt")
except:
    flag = False

predictions = []
if flag:
    for element in elements:
        try:
            prb = element.find("div", class_="fprc").find_all("span")
            predictions.append({
            "league_flag": element.find("img", class_="flsc").get("src"),
            "home_team": element.find("span", class_="homeTeam").find("span").text,
            "away_team": element.find("span", class_="awayTeam").find("span").text,
            "date_time": element.find("span", class_="date_bah").text,
            "home_prb": prb[0].text,
            "draw_prb": prb[1].text,
            "away_prb": prb[2].text,
            "home_score": element.find("div", class_="ex_sc tabonly").text.split(" ")[0],
            "away_score":element.find("div", class_="ex_sc tabonly").text.split(" ")[2],
            "time_played":element.find("span", class_="l_min").text
        })
        except:
            pass
print(predictions)
print(len(predictions))