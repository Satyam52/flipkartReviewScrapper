from flask import Flask, render_template, url_for, request, redirect, jsonify, json
import requests
from datetime import datetime
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
from bson.json_util import dumps

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        searchString = request.json['content']
        try:
            # opening a connection to Mongo
            try:
                dbConn = pymongo.MongoClient(
                    "mongodb+srv://Satyam52:Satyam03@cluster0.fsdvz.mongodb.net/<dbname>?retryWrites=true&w=majority")
                db = dbConn['crawlerDB']
            except Exception as e:
                print(e)
                return "DataBase Error", 404

            reviews = db[searchString].find({})
            if reviews.count() > 0:
                return dumps(reviews), 200
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + \
                    searchString.strip()
                flipkart_url = flipkart_url.replace(" ", "-")
                uClient = uReq(flipkart_url)
                flipkartPage = uClient.read()
                uClient.close()
                flipkart_html = bs(flipkartPage, "html.parser")
                bigboxes = flipkart_html.findAll("div", {"class": "_1UoZlX"})
                box = bigboxes[0]
                productLink = "https://www.flipkart.com" + box.a['href']
                prodRes = requests.get(productLink)
                prodRes.encoding = 'utf-8'
                prod_html = bs(prodRes.text, "html.parser")
                commentboxes = prod_html.find_all('div', {'class': "_3nrCtb"})
                table = db[searchString]
                filename = searchString+".csv"
                fw = open(filename, "w")
                headers = "Product, Customer Name, Rating, Heading, Comment \n"
                fw.write(headers)
                reviews = []
                for commentbox in commentboxes:
                    try:
                        name = commentbox.div.div.find_all(
                            'p', {'class': '_3LYOAd _3sxSiS'})[0].text

                    except:
                        name = "No Name"

                    try:
                        rating = commentbox.div.div.div.div.text

                    except:
                        rating = "No Rating"

                    try:
                        commentHead = commentbox.div.div.div.p.text

                    except:
                        commentHead = "No Comment Heading"
                    try:
                        comtag = commentbox.div.div.find_all(
                            'div', {'class': ''})
                        custComment = comtag[0].div.text
                    except:
                        custComment = "No Customer Comment"

                    try:
                        fw.write(searchString+","+name.replace(",", ":")+","+rating + "," +
                                 commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                    except:
                        pass
                    mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                              "Comment": custComment}
                    x = table.insert_one(mydict)
                    reviews.append(mydict)
                return dumps((i) for i in reviews[0:len(reviews)-1]), 200

        except Exception as e:
            print(e)
            return "BaseException", 400


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
