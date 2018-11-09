from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import requests
import os
import json
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
#specify developer credentials and redirect uri for spotify
# Create your views here.
def index(request):
    return HttpResponse('Hello, welcome to the index page.')

# def redirect(request):
#     return HttpResponse(str(request.build_absolute_uri()))
#
def spotlogin(request):
    ''' prompts the user to login if necessary and returns
        the user token suitable for use with the spotipy.Spotify
        constructor
        Parameters:
         - username - the Spotify username
         - scope - the desired scope of the request
         - client_id - the client id of your app
         - client_secret - the client secret of your app    
         - redirect_uri - the redirect URI of your app
         - cache_path - path to location to save tokens
    '''
    client_id = '327541285c7343afbf4822dc9d30ef7f'
    client_secret = '713dbe89b2ea4bd382fb0a7b366a63bb'
    redirect_uri = 'http://smalldata411.web.illinois.edu/redirect'
    cache_path = None
    username = 'sahil5'          #hardcoded now...change for later
    scope = 'user-library-read'
    if not client_id:
        client_id = os.getenv('SPOTIPY_CLIENT_ID')

    if not client_secret:
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

    if not redirect_uri:
        redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

    if not client_id:
        print('''
            You need to set your Spotify API credentials. You can do this by
            setting environment variables like so:
            export SPOTIPY_CLIENT_ID='your-spotify-client-id'
            export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
            export SPOTIPY_REDIRECT_URI='your-app-redirect-url'
            Get your credentials at
                https://developer.spotify.com/my-applications
        ''')
        raise spotipy.SpotifyException(550, -1, 'no credentials set')

    cache_path = cache_path or ".cache-" + username
    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri,
        scope=scope, cache_path=cache_path)

    # try to get a valid token for this user, from the cache,
    # if not in the cache, the create a new (this will send
    # the user to a web page where they can authorize this app)

    token_info = sp_oauth.get_cached_token()

    if not token_info:
        print('''
            User authentication requires interaction with your
            web browser. Once you enter your credentials and
            give authorization, you will be redirected to
            a url.  Paste that url you were directed to to
            complete the authorization.
        ''')

        auth_url = sp_oauth.get_authorize_url()
        #attempt to open the authorize url. This will redirect to our redirect page upon login
        try:
            # import webbrowser
            # webbrowser.open_new_tab(auth_url)
            #return HttpResponse("OPENED: " + str(auth_url))
            return HttpResponseRedirect(str(auth_url))

        except:
            return HttpResponse("FAILED")

def finish_spot_auth(request):
    c = connections['default'].cursor()
    client_id = '327541285c7343afbf4822dc9d30ef7f'
    client_secret = '713dbe89b2ea4bd382fb0a7b366a63bb'
    redirect_uri = 'http://smalldata411.web.illinois.edu/redirect'
    cache_path = None
    username = 'sahil5'          #hardcoded now...change for later
    scope = 'user-library-read'
    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=cache_path)
    response = str(request.build_absolute_uri())
    code = sp_oauth.parse_response_code(response)
    token_info = sp_oauth.get_access_token(code)
    token = token_info['access_token']
    # # Auth'ed API request
    client_credentials_manager = SpotifyClientCredentials(client_id = client_id, client_secret= client_secret)
    
    if token:
        sp = spotipy.Spotify(auth=token, client_credentials_manager=client_credentials_manager)
        results = sp.current_user_saved_tracks(limit=50) #max limit is fifty songs...use paging to scroll through results
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items']) #tracks is a list
        values = list()
        songID = 0
        for track in tracks:
            song = track['track']
            name = song['name']
            #quote in name braks errything
            artist  = song['artists'][0]['name']
            if "'" in name or "'" in artist:
                continue
            #check if song, artist, and service combination already exist in the DB
            command  = "SELECT UniqueSongID FROM TopSongsMeta WHERE service = \"Spotify\" and artist = \"" + str(artist) + "\" and title = \"" + str(name) +"\""
            c.execute(command, [])
            rows = c.fetchall()
            if(len(rows) == 0):
                continue
            tuple = "("
            tuple  += "1, "
            tuple += "'Spotify', "
            tuple += "'" + str(artist) +"', "
            tuple += "'" + str(name) +"', "
            tuple += str(songID)
            tuple += ")"
            values.append(tuple)
            songID = songID + 1
        insert_a_lot('TopSongsMeta', '(UserID, Service, Artist, Title, UniqueSongID)', values)
        return HttpResponseRedirect("http://smalldata411/web/illinois.edu")
    else:
        return HttpResponse("ERROR")
   # return HttpResponse(str(token_info))
    
    
    
# SAHIL, I made the 'insert_a_lot' function for you. 
# Pass it the name of the table as a string (e.g. 'Users'), the attributes as
# a string (e.g. '(UserID, FirstName, LastName, NumberOfAccounts)') and the 
# values as a list of strings... however make sure to put the string values in
# single quotes inside of the string (otherwise it won't work)!! E.g. : 
#  lst = ["(4, 'Avery','Apple', 20)", "(5, 'Sandra', 'Strawberry', 10)", "(6, 'Ben', 'Banana', 3)"]
# before inserting, verify that data does not already exists in the DB
 
def insert_a_lot(tableName,tableAttributes,values):
    c = connections['default'].cursor()
    sql_syn = "INSERT INTO "
    sql_syn+= tableName + " " + tableAttributes +  " VALUES "
    for i in range(len(values)):
        sql_syn += values[i]
        if(i< len(values)-1):
            sql_syn+=" , "
    sql_syn += ";"
    c.execute(sql_syn,[])
    
# INSET INTO TopSongsMeta (UserID, Service, Artist, Title, UniqueSongID)


def searchQuery(request):
    #How to connect to the database and display 
    #Build an HTML page response
    search_value = request.GET.get("SearchVal","") 
    search_table = request.GET.get("SearchTable","")
    search_attributes = request.GET.get("Attributes","")
    c = connections['default'].cursor()
    sql_syn = ""
    if(',' in search_attributes):
        #sql_syn = "SELECT * FROM " + search_table + " WHERE " + search_value + " IN " + search_attributes + ";"
        sql_syn = "SELECT * FROM " + search_table +  " WHERE %s IN " + search_attributes + ";"
    else:
        #sql_syn = "SELECT * FROM " + search_table + " WHERE " + search_attributes + " = " + search_value + ";"   
        sql_syn = "SELECT * FROM " +search_table+  " WHERE " +search_attributes+ "= %s;"
    
    response = HttpResponse("Failure")
    try:
        c.execute(sql_syn,[search_value])
        rows = c.fetchall()
        if (len(rows) != 0):
            response = HttpResponse(rows)
        response = HttpResponse("No Results")
    except:
        response = HttpResponse("No Results")
            
    return response
    

    
def insertQuery(request):
    insert_table = request.GET.get("InsertTable","")
    insert_attributes = request.GET.get("InsertAttributes","")
    insert_values = request.GET.get("InsertValues")
    c = connections['default'].cursor()
    sql_syn = "INSERT INTO " + insert_table + " " + insert_attributes + " VALUES " + insert_values + ";" 
    c.execute(sql_syn,[])
    rows = c.fetchall()
    response = HttpResponse("Ran\n" + sql_syn + "successfully")
    
    return response
    
def updateQuery(request):
    c = connections['default'].cursor()
    update_table = request.GET.get("UpdateTable","")
    update_attributes = request.GET.get("UpdateAttributes","")
    update_values = request.GET.get("UpdateValues","")
    update_condition = request.GET.get("UpdateCondition","")
    
    sql_syn = "UPDATE " + update_table + " SET " + update_attributes + " = " + update_values + " WHERE " + update_condition
    
    c.execute(sql_syn,[])
    response = HttpResponse(sql_syn + "SUCCESS")
    return response 

def deleteQuery(request):
    c = connections['default'].cursor()
    delete_table = request.GET.get("DeleteTable","")
    delete_attributes = request.GET.get("DeleteAttributes","")
    delete_condition = request.GET.get("DeleteCondition","")
    
    sql_syn = "DELETE FROM " + delete_table + " WHERE " + delete_attributes + delete_condition

    c.execute(sql_syn,[])
    response = HttpResponse(sql_syn + "SUCCESS")
    return response     