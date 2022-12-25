from flask import Flask, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage , ImageMessage, ImageSendMessage
import os
import tempfile
import cv2
import numpy as np
from matplotlib import pyplot as plt


def boundRec(contours):
       X, Y, W, H = 0, 0, 0, 0
       for i, cnt in enumerate(contours):
          x,y,w,h = cv2.boundingRect(cnt)
          if w>W and h>H :
            X = x
            Y = y
            W = w
            H = h
       return X, Y, W, H


channel_secret = "2d3ee0663a6a56f81cc0871777306518"
channel_access_token = "EyAY4p/HLIazNPl3RBfbcuvbXWq10MQll7psEUUvAs2CXYRhyxyRrh0stN4uZzNGIqtxg9zJFUYdHxdwCSSvR/xIi0CQTfm3aT9owvEGUCRV75HsKux+LIgbZdsm5L7Z8vfChpoOPhgVBzUozfnGQAdB04t89/1O/w1cDnyilFU="

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

@app.route("/", methods=["GET","POST"])
def home():
    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)
    except:
        pass
    
    return "Hello Lab Chatbot"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp').replace("\\","/")
    print(static_tmp_path)
    
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='jpg' + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name
        
    dist_path = tempfile_path + '.jpg'  # เติมนามสกุลเข้าไปในชื่อไฟล์เป็น jpg-xxxxxx.jpg
    os.rename(tempfile_path, dist_path) # เปลี่ยนชื่อไฟล์ภาพเดิมที่ยังไม่มีนามสกุลให้เป็น jpg-xxxxxx.jpg

    filename_image = os.path.basename(dist_path) # ชื่อไฟล์ภาพ output (ชื่อเดียวกับ input)
    filename_fullpath = dist_path.replace("\\","/")   # เปลี่ยนเครื่องหมาย \ เป็น / ใน path เต็ม
    
    img = cv2.imread(filename_fullpath)    # Read the input image
    
    # ใส่โค้ดประมวลผลภาพตรงส่วนนี้
    #---------------------------------------------------------

    org = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    # convert the image to grayscale
    blur = cv2.GaussianBlur(gray,(5,5),0)
    ret,thresh = cv2.threshold(blur,200,400,0)   # apply thresholding to convert grayscale to binary image


    contours,hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)    # find the contours
    #print("Number of objects detected:", len(contours))


    # find boundary rectangle
    x,y,w,h = boundRec(contours)
    rectArea = (w)*(h)
    img = cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)


    # draw contours and sum area of contours
    sum_area = 0
    for i, cnt in enumerate(contours):
       M = cv2.moments(cnt)
       if M['m00'] != 0.0:
          x1 = int(M['m10']/M['m00'])
          y1 = int(M['m01']/M['m00'])
       area = cv2.contourArea(cnt)
       sum_area = sum_area + area
       img = cv2.drawContours(img, [cnt], -1, (0,255,0), 1)
   
    ratio = int(sum_area/rectArea*100)

    if ratio > 65 :
      result ='0B'
    elif ratio > 35 :
      result ='1B'
    elif ratio > 15 :
      result ='2B'
    elif ratio > 5 :
      result ='3B'
    elif ratio > 0 :
      result ='4B'
    else:
      result ='5B'

    #print(f'Sum Area of contour :', sum_area)
    #print(f'Boundary Area :', rectArea)
    cv2.putText(img, f'%Peel off ={ratio}', (x, y-80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
    cv2.putText(img, f'Result ={result}', (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
    #cv2.imshow("Result",img)


    
    #---------------------------------------------------------    
    cv2.imwrite(filename_fullpath,img)
    
    dip_url = request.host_url + os.path.join('static', 'tmp', filename_image).replace("\\","/")
    print(dip_url)
    line_bot_api.reply_message(
        event.reply_token,[
            TextSendMessage(text='ประมวลผลภาพเรียบร้อยแล้ว Result = ' + result),
            ImageSendMessage(dip_url,dip_url)])
    
@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

if __name__ == "__main__":          
    app.run()

