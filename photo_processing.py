# -*- coding: utf-8 -*-

def total_score(photo):
    photo_score = {"anger":0,"contempt":0,"disgust":0,"fear":0,"happiness":0,"neutral":0,"sadness":0,"surprise":0}
    n_photos = len(photo)

    for face in photo:
        photo_score["anger"]     += face["scores"]["anger"]
        photo_score["contempt"]  += face["scores"]["contempt"]
        photo_score["disgust"]   += face["scores"]["disgust"]
        photo_score["fear"]      += face["scores"]["fear"]
        photo_score["happiness"] += face["scores"]["happiness"]
        photo_score["neutral"]   += face["scores"]["neutral"]
        photo_score["sadness"]   += face["scores"]["sadness"]
        photo_score["surprise"]  += face["scores"]["surprise"]
    for emotion in photo_score:
        photo_score[emotion] /= n_photos 
    
    return [photo_score]

def photo_metadata(vision):
    ''' Return the information of age and gender
    '''
    metadata = []
    for face in vision["faces"]:
        metadata.append({"gender": face["gender"], "age": face["age"]})
        
    return metadata