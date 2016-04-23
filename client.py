# Programa cliente do jogo do galo em UDP - Python 3
# Comandos que se pode enviar:
#  registar nome
#  lista
#  convidar jogador
#  jogar posição
#  sair
#
#  registar - nome
#  lista
#  convidar - src - dst
#  jogar - src - dst - pos
#  sair
#
# Comandos automatizados
#  OK
#  RCONVIDAR - src - dst - resp
#  OK - src - dst 
#  NOK - src - dst
#  FIM - src - dst - v/d/e

import socket
import sys
import select
import signal

SERVER_PORT = 12000
SERVER_IP   = '127.0.0.1'
SEND_TIME   = 2

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

retries = 0
name = ""
opponent = ""
flag_registar = False
flag_convidar = False
flag_sair = False
flag_convidar_pedido = False
flag_em_jogo = False

# o select quer ficar a espera de ler o socket e ler do stdin (consola)
inputs = [sock, sys.stdin]

#funções do jogo do galo
def print_board(board):

  for i in range(3):
    print(" ", end="")
    for j in range(3):
      if board[i*3+j] == 1:
        print('X', end="")
      elif board[i*3+j] == 0:
        print('O', end="")
      elif board[i*3+j] != -1:
        print(" ", end="")
      else:
        print(" ", end="")

      if j != 2:
        print(" | ", end="")
    print()

    if i != 2:
      print("---+---+---")
    else:
      print()

def get_input(turn): #verifica se a jogada é de 1 a 9

  valid = False
  while not valid:
    try:
      user = input("Escolha a sua jogada de 1 a 9 (símbolo " + turn + "). ")
      user = int(user)
      if user >= 1 and user <= 9:
        return user-1
      else:
        print("Jogada inválida! Escolha uma posição válida de 1 a 9.\n")
    except Exception as e:
      print("Jogada inválida. Tente de novo.\n")

def check_win(board): #devolve o jogador vencedor
  win_cond = ((1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7))
  for each in win_cond:
    try:
      if board[each[0]-1] == board[each[1]-1] and board[each[1]-1] == board[each[2]-1]:
        return board[each[0]-1]
    except:
      pass
  return -1

def galomain(arg):
  # Start Game
  # Change turns
  # Check for winner
  # Quit and redo board
  global name
  global opponent
  global sentmsg
  flag_playing = arg

  board = []
  for i in range(9):
    board.append(-1)

  win = False
  move = 0

  while not win:
    # Print board
    print_board(board)
    print("Turno nº " + str(move+1))
    if move % 2 == 0:
      turn = 'X'
    else:
      turn = 'O'
    # Get player input
    # if playing, pede input, if waiting, recebe input
    if flag_playing == True:
      user = get_input(turn)
      #envia jogada ao outro jogador
      playMsg = "JOGAR|"+ name + "|" + opponent + "|" + str(user) + "|"
      sentmsg = playMsg
      sock.sendto(playMsg.encode(),(SERVER_IP,SERVER_PORT))
      signal.alarm(SEND_TIME)
      #recebe resposta
      (msg,addr) = sock.recvfrom(1024)
      signal.alarm(0)
      serverMsg = msg.decode().split('|')
      if serverMsg[0] == "NOK":
        print("Jogada inválida: posição ocupada")
      elif serverMsg[0] == "FIM":
        board[user] = 1 if turn == 'X' else 0
        print_board(board)
        if serverMsg[3] == "V":
          print("Ganhou!")
        elif serverMsg[3] == "E":
          print("Empate!")
        elif serverMsg[3] == "D":
          print("Perdeu!")
        win = True
        playResponseMsg = "OK|" + name + "|" + opponent + "|"
        sentmsg = playResponseMsg
        sock.sendto(playResponseMsg.encode(),(SERVER_IP,SERVER_PORT))

      elif serverMsg[0] == "OK":
        #a jogada foi aceite e agora o cliente espera
        board[user] = 1 if turn == 'X' else 0
        flag_playing = False
        move += 1
    
    #envia jogada para o outro jogador
    elif flag_playing == False:
      #recebe resposta
      print("Espere pela jogada do jogador adversário.")
      (msg,addr) = sock.recvfrom(1024)
      serverMsg = msg.decode().split('|')
      #interpreta a mensagem para ver se é válida
      user = serverMsg[3]
      if board[int(user)] != -1:
        playResponseMsg = "NOK|" + name + "|" + opponent + "|"
        sock.sendto(playResponseMsg.encode(),(SERVER_IP,SERVER_PORT))
      else:
        board[int(user)] = 1 if turn == 'X' else 0
        move += 1
        winner = -1
        if move > 4:
          winner = check_win(board) #checkwin devolve -1 para não haver vencedor
          if winner != -1: #quem começa é o X - 1, O - 0
            if winner == 1:
              playResponseMsg = "FIM|" + name + "|" + opponent + "|V|"
              print("Perdeu!")
            elif winner == 0:
              playResponseMsg = "FIM|" + name + "|" + opponent + "|D|"
              print("Ganhou!")
          elif move == 9:
            playResponseMsg = "FIM|" + name + "|" + opponent + "|E|"
            print("Empate!")
        else:
          playResponseMsg = "OK|" + name + "|" + opponent + "|"

        sentmsg = playResponseMsg
        sock.sendto(playResponseMsg.encode(),(SERVER_IP,SERVER_PORT))
        flag_playing = True
        if winner == 1 or winner == 0 or move == 9: #e preciso esperar pelo ok do outro jogador em caso de fim de jogo
          signal.alarm(SEND_TIME)
          (msg,addr) = sock.recvfrom(1024) # recebeu o ok do outro cliente
          signal.alarm(0)
          win = True
        #envia mensagem ok para o outro jogador ou envia FIM. se enviar FIM, espera por um ok
    

  # Fim do loop do jogo do galo

#------------------------------------------------------------------------------

def signal_handler(signum, frame):
  global retries
  if retries <3:
    sock.sendto(sentmsg.encode(),(SERVER_IP,SERVER_PORT))
    retries+= 1
    signal.alarm(SEND_TIME)
  else:
    print("Servidor indisponível")
    retries = 0

def sigint_handler(signum, frame):
  print("\nCliente a encerrar forçadamente...")
  sock.sendto("SAIR".encode(),(SERVER_IP,SERVER_PORT))
  quit()

signal.signal(signal.SIGALRM, signal_handler)

signal.signal(signal.SIGINT, sigint_handler)

while True:
  ins, outs, exs = select.select(inputs,[],[])
  #select devolve para a lista ins quem esta a espera de ler
  for i in ins:
    # i == sys.stdin - alguem escreveu na consola, vamos ler e enviar
    if i == sys.stdin:
      # sys.stdin.readline() le da consola
      msg = sys.stdin.readline().split(" ")
      msgToServer = ""

      #analisar a mensagem inputada
      print(msg)
      #regista - nome
      if msg[0].lower() == "registar":
        name = str(msg[1]).strip('\n')
        msgToServer = "REGISTAR|" + name
        flag_registar = True

      elif msg[0].lower() == "convidar":
        msgToServer = "CONVIDAR" + "|" + name + "|" + msg[1].lower().strip('\n')
        flag_convidar = True
        
      elif msg[0].lower() == "lista\n":
        msgToServer = "LISTA"
        
      elif msg[0].lower() == "sair\n":
        msgToServer = "SAIR"
        flag_sair = True

      elif msg[0].lower() == "s\n" or msg[0].lower() =="n\n":
        if flag_convidar_pedido == True:
          msgToServer = "RCONVIDAR|" + src + "|" + dst + "|" + msg[0].upper().strip('\n')
        else:
          print("Erro: Comando inválido. Não foi recebido nenhum convite.")
          continue
      else:
        print("Erro: Comando inválido")
        continue

      # envia mensagem da consola para o servidor
      sentmsg = msgToServer
      sock.sendto(msgToServer.encode(),(SERVER_IP,SERVER_PORT))
      signal.alarm(SEND_TIME)

    # i == sock - o servidor enviou uma mensagem para o socket
    elif i == sock:
      (msg,addr) = sock.recvfrom(1024)
      serverMsg = msg.decode().split('|')

      # Recebe OK ou NOK
      if serverMsg[0] == "OK":
        signal.alarm(0)
        if flag_registar == True:
          print("Registo com o nome " + name + " bem efetuado.")
          flag_registar = False
        elif flag_sair == True:
          print("Saída efetuada com sucesso.")
          quit()
        elif flag_convidar == True:
          print("Pedido enviado.")
          flag_convidar = False
        elif flag_convidar_pedido == True:
          print("Resposta enviada com sucesso.")
          flag_convidar_pedido = False
          if 'S' in msgToServer:
            galomain(False)
      elif serverMsg[0] == "NOK":
        signal.alarm(0)
        #se o cliente nao estiver registado mas ainda assim quiser sair
        if flag_sair == True:
          quit()
        if flag_convidar == True:
          flag_convidar = False
          print("Erro: " + serverMsg[1])
        else:
          print("Erro: " + serverMsg[1])

      # Recebe convite
      elif serverMsg[0] == "CONVIDAR":
        clientResponse = "OK|" + serverMsg[2] + "|" + serverMsg[1]
        sock.sendto(clientResponse.encode(),(SERVER_IP,SERVER_PORT))
        opponent = serverMsg[1]
        print("Recebeu um convite de jogo do jogador " + opponent + ". Deseja aceitar? [S/N]")
        flag_convidar_pedido = True
        
        #valores já para a resposta
        dst = serverMsg[1] 
        src = serverMsg[2]

      # Recebe resposta de lista
      elif serverMsg[0] == "RLISTA":
        signal.alarm(0)

        #envia o OK ao servidor
        clientResponse = "OK|"
        sock.sendto(clientResponse.encode(),(SERVER_IP,SERVER_PORT))

        #imprime a lista no ecra
        size = len(serverMsg)
        print("---Lista de jogadores---")
        for i in range (1, size-1):
          line = serverMsg[i].split(':')
          print(line[0] + " - " + line[1])
        print("------------------------")

      #recebe resposta ao convite
      elif serverMsg[0] == "RCONVIDAR":
        #envia a confirmação ao servidor exceto em caso de NA (resposta automática do servidor)
        if serverMsg[3] == "S":
          opponent = serverMsg[1]
          clientResponse = "OK|" + serverMsg[2] + "|" + serverMsg[1]
          sock.sendto(clientResponse.encode(),(SERVER_IP,SERVER_PORT))
          print("Convite aceite.")
          galomain(True)
        elif serverMsg[3] == "NA":
          signal.alarm(0)
          print("Este jogador encontra-se numa partida. Espere um pouco e tente de novo.")
          continue
        else:
          print("Convite recusado.")
          clientResponse = "OK|" + serverMsg[2] + "|" + serverMsg[1]
          sock.sendto(clientResponse.encode(),(SERVER_IP,SERVER_PORT))