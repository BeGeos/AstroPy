# AstroPy

An API for astronomy enthusiasts. The logic behind it is quite straightforward. Just type in the query URL a name of a constellation and you receive a JSON response 
with the most significant and important information about said constellation, namely:
- Right Ascension and Declination, essential for observation
- Minimium and Maximum Latitude where that constellation can be seen
- The main stars that comprise the constellation


# Last Update

I have decided to move all the user related information, login, verification, etc. to the website.
Now, the website has the main database for user information and communicates to the api for the authentication 
keys via restricted routes. In this way the main website manages all the user data, whereas the API deals with
the bulk information about stars/planets/constellations

If you are interested visit my repo named 'Pystronomical'. There, you'll find the basic framework for my new website.

@BeGeos
