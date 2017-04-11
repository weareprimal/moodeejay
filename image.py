#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httplib, urllib, base64, json, os

def process_image(url):
    headers_emotion = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': os.environ["MS_EMOTION"],
    }

    headers_vision = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': os.environ["MS_VISION"],
    }

    params_emotion = urllib.urlencode({
    })

    params_vision = urllib.urlencode({
        # Request parameters
        'visualFeatures': 'Faces',
    })


    body ="{'url':'" + url + "'}"

    #emotion api
    try:
        conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
        conn.request("POST", "/emotion/v1.0/recognize?%s" % params_emotion, body, headers_emotion)
        response = conn.getresponse()
        print str(response.status) + " " + response.reason
        data = json.load(response)
        if len(data) == 0:
            raise Exception('Error: No faces')
        conn.request("POST", "/vision/v1.0/analyze?%s" % params_vision, body, headers_vision) #compute_vision
        response = conn.getresponse()
        vision = json.load(response)
       # print vision
        conn.close()
        return [data, vision]
    except Exception as e:
        print e
        return False
    #    print("[Errno {0}] {1}".format(e.errno, e.strerror))
    ####################################