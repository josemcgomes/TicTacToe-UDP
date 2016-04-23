# TicTacToe-UDP
Tic Tac Toe game using UDP
This was made for a university project delivered on the 20th of April, 2015. UDP was chosen because the goal of the project was to implement reliability on an application level
Made on OS X. Last time I checked, didn't work on Linux.


#####To do:
- Make it work on Linux
- Implement the main loop on a function so it can be called from SIGINT handler
- Correct timeout handling while on a game, checking if the user is available every time
- Implement logging in and out, letting other users know whether someone is offline, online or online and playing
- Implement exception handling for better reliability 
- Implement a way of handling player list transmission when the player list is too large.
