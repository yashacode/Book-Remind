import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import requests
import random

NOTION_TOKEN = "YOUR TOKEN"
DATABASE_ID = "YOUR DATABASE ID"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

#sends your email summary
def lambda_handler(event, context):
 
    message = MIMEMultipart()
    message["To"] = 'mr.YOURNAME'
    message["From"] = 'YOURNAME@gmail.com'
    message["Subject"] = 'goodmorning'

    book = get_random_book()
    content = f"""good afternoon YOURNAME!\n\nToday we have {book['title']}
            by {book['author']}{book['contents']}"""
   
    body = f"<html><head></head><body>{content}<br></body></html>"
    messageText = MIMEText(body,'html')
    message.attach(messageText)

    email = 'YOURNAME@gmail.com'
    password = 'YOUR PASSWORD'

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo('Gmail')
    server.starttls()
    server.login(email,password)
    fromaddr = 'YOURNAME@gmail.com'
    toaddrs  = 'YOURFRIEND@gmail.com'
    server.sendmail(fromaddr,toaddrs,message.as_string())
    server.quit()


def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = data["results"]

    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])
        

    return results

# converts JSON book summary to html
def block_to_html(block):
    block_type = block['type']
    html = ""

    if block_type == 'paragraph':
        html += "<p>"
        for text in block[block_type]['rich_text']:
            html += text['plain_text']
        html += "</p>"
    elif block_type == 'heading_1':
        html += f"<h1>{block[block_type]['rich_text'][0]['text']['content']}</h1>"
    elif block_type == 'heading_2':
        html += f"<h2>{block[block_type]['rich_text'][0]['text']['content']}</h2>"
    elif block_type == 'heading_3':
        html += f"<h3>{block[block_type]['rich_text'][0]['text']['content']}</h3>"
    elif block_type == 'bulleted_list_item':
        html += "<li>"
        print(block[block_type]['rich_text'][0])
        html += block[block_type]['rich_text'][0]['text']['content']
        html += "</li>"
    elif block_type == 'numbered_list_item':
        html += "<li>"
        html += block[block_type]['rich_text'][0]['text']['content']
        html += "</li>"
    elif block_type == 'to_do':
        checked = "checked" if block[block_type]['checked'] else ""
        html += f'<input type="checkbox" {checked} disabled>'
        for text in block[block_type]['text']:
            html += text['plain_text']

    if 'children' in block:
        for child in block['children']:
            html += block_to_html(child)

    return html


# returns dictionary containing book info from random book
def get_random_book():
    bookInfo = {}
    random.seed()
    pages = get_pages()
    i = 0
    #chose a book that has been read
    while True:
        x = random.randrange(len(pages))
        if pages[x]['properties']['Status']['select']['name'] == 'Finished':
            i = x
            break

    #change i to get page w bold, images, links etc...
    page = pages[i]

    # get the author, title, and contents of the book
    bookInfo['title'] = page['properties']['Name']['title'][0]['text']['content']
    bookInfo['author'] = page['properties']['Author']['multi_select'][0]['name']
    bookInfo['contents'] = ''
    page_id = page["id"]
    url = "https://api.notion.com/v1/blocks/" + page_id + "/children?page_size=100"
    response = requests.get(url, headers=headers)
    
    for part in response.json()['results']:
        bookInfo['contents']+=(block_to_html(part))

    return bookInfo
