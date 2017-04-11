import httplib, urllib, base64, json

def process_text(text):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': os.environ["MS_SENTIMENT"],
    }

    params = urllib.urlencode({
        # Request parameters
        'numberOfLanguagesToDetect': '{integer}',
    })

    params_sent = urllib.urlencode({
    })

    body = "{'documents': [{'id': 'string','text': '" + text + "'}]}"

    try:
        conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
        conn.request("POST", "/text/analytics/v2.0/languages?%s" % params, body, headers)
        response = conn.getresponse()
        data = json.load(response)
        language = data["documents"][0]["detectedLanguages"][0]["name"]

        body_sent = "{'documents': [{'language':" 
        if language == "Spanish":
            body_sent += "'es'"
        elif language == "English":
            body_sent += "'es'"
        else:
            raise Exception('Language Error')

        body_sent += ",'id': 'string','text': '" + text + "'}]}"     
      #  print body_sent
        conn.request("POST", "/text/analytics/v2.0/sentiment?%s" % params_sent, body_sent, headers)  
        response = conn.getresponse()
        sent = json.load(response)         
        score = sent["documents"][0]["score"]
        conn.close()
        return score
    except Exception as e:
        print e
     #   print("[Errno {0}] {1}".format(e.errno, e.strerror))