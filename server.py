# Programa servidor do jogo do galo com UDP - Python 3
#
# Comandos que recebe
# Registar
# Lista
# Sair
# Convidar
# Jogar
# Fim

#-----Init-----
import socket
import signal
SERVER_PORT=12000

server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server.bind(('',12000))

addrs   = {} # dict: nome -> endereco. Ex: addrs["user"]=('127.0.0.1',17234)
clients = {} # dict: endereco -> nome. Ex: clients[('127.0.0.1',17234)]="user"
state = {}   # dict: nome -> estado.   Ex: state["user"]="livre"
prev_cmds = []
repeat = 0   # used to check whether a client is sending repeated invites to another client
lastmsg = ""

def sigint_handler(signum, frame):
  print("\nServidor a encerrar...")
  quit()

signal.signal(signal.SIGINT, sigint_handler)

#------Funcoes utilizadas-----
def register_client(name,addr):
  # se o nome nao existe e o endereco nao esta a ser usado
  if not name in addrs and not addr in clients:
    addrs[name] = addr
    clients[addr] = name
    state[name] = 'Livre'
    respond_msg = "OK"
  
  else:
    respond_msg = "NOK|Utilizador já registado!"
  
  server.sendto(respond_msg.encode(), addr)

def remove_client(addr):
  if addr in clients:
    removed_name = clients[addr]
    del addrs[removed_name]
    del state[removed_name]
    del clients[addr]
    respond_msg = "OK"
  else:
    respond_msg = "NOK|Utilizador não registado!"

  server.sendto(respond_msg.encode(), addr)
  print("removed")

def list_clients(addr):
  # devolve a lista de clientes se o calling client estiver registado
  if addr in clients: 
  # if bool(state):
    respond_msg = "RLISTA|"
    for name in state:
      respond_msg = respond_msg + name + ":" + state[name] + "|"
  
  else:
    respond_msg = "NOK|Acesso negado."

  server.sendto(respond_msg.encode(),addr)

def handle_invite(addr, sender, receiver):
  global lastmsg
  global repeat
  if sender == receiver:
    respond_msg = "NOK|Não se pode convidar a si próprio!"
    server.sendto(respond_msg.encode(), addr)
  else:
    if receiver in state:
      if state[receiver] == "Ocupado":
        respond_msg = "RCONVIDAR|" + receiver + "|" + sender + "|NA|"
        print("user ocupado")
        server.sendto(respond_msg.encode(), addr)
      
      elif state[receiver] == "Livre":
        respond_msg = "CONVIDAR|" + sender + "|" + receiver
        if lastmsg == respond_msg:
          repeat += 1
        else:
          lastmsg = respond_msg 
        if repeat == 3:
          respond_msg = "NOK|Cliente indisponível"
          server.sendto(respond_msg.encode(), addrs[sender])
          remove_client(addrs[receiver])
          repeat = 0
        else:
          server.sendto(respond_msg.encode(), addrs[receiver])
          print(addrs[receiver])

    else:
      respond_msg = "NOK|Jogador não encontrado"
      server.sendto(respond_msg.encode(), addr)

def handle_invite_response(addr, sender, receiver, response):
  respond_msg = "RCONVIDAR|" + sender + "|" + receiver + "|" + response + "|"
  if response == 'S':
    state[sender] = 'Ocupado'
    state[receiver] = 'Ocupado'
  server.sendto(respond_msg.encode(), addrs[receiver])

def handle_ok(sender, receiver):
  respond_msg = "OK|" + sender + "|" + receiver + "|"
  server.sendto(respond_msg.encode(), addrs[receiver])

def handle_nok(sender, receiver):
  respond_msg = "NOK|" + sender + "|" + receiver + "|"
  server.sendto(respond_msg.encode(), addrs[receiver])

def handle_play(sender, receiver, play):
  respond_msg = "JOGAR|" + sender + "|" + receiver + "|" + play + "|"
  server.sendto(respond_msg.encode(), addrs[receiver])

def handle_end(sender, receiver, result):
  respond_msg = "FIM|" + sender + "|" + receiver + "|" + result + "|"
  state[sender] = 'Livre'
  state[receiver] = 'Livre'
  server.sendto(respond_msg.encode(), addrs[receiver])

def respond_error(addr):
  respond_msg = "NOK|Mensagem inválida"
  server.sendto(respond_msg.encode(),addr)


#------Main Loop-----

while True:
  (msg,addr) = server.recvfrom(1024)
  cmds = msg.decode().split('|')
  print(cmds)
  # print(addr)

  if(cmds[0]=='REGISTAR'):
    register_client(cmds[1],addr)

  elif(cmds[0]=='SAIR'):
    remove_client(addr)

  elif(cmds[0]=='LISTA'):
    list_clients(addr)

  elif(cmds[0]=="CONVIDAR"):
    handle_invite(addr, cmds[1], cmds[2])

  elif(cmds[0]=="RCONVIDAR"):
    handle_invite_response(addr, cmds[1], cmds[2], cmds[3])
  
  elif(cmds[0]=="OK"):
    if cmds[1]!="":
      handle_ok(cmds[1], cmds[2])

  elif(cmds[0]=="NOK"):
    handle_nok(cmds[1], cmds[2])

  elif(cmds[0]=="JOGAR"):
    handle_play(cmds[1], cmds[2], cmds[3])

  elif(cmds[0]=="FIM"):
    handle_end(cmds[1], cmds[2], cmds[3])
  
  else:
    respond_error(addr)


server.close()