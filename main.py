'''
Universidade Federal de Pernambuco (UFPE) (http://www.ufpe.br)
Centro de Informática (CIn) (http://www.cin.ufpe.br)
Disciplina: IF975 - Redes de Computadores
Curso: Sistemas de Informação
Data: 06/12/2019
Autores: Alisson Diego Diniz D. da Fonseca (adddf)
         Lucas do Carmo Barbosa (lcb3)
         Luiz Henrique Pedrozo Vieira (lhpv)
         Pedro Manoel Farias Sena de Lima (pmfsl)
         José Rudá Alves do Nascimento (jran)
'''


from server import *
from room import *
from client import *
import time

def startPeer():
    global lock  # Variável utilizada para processar separadamente os pedidos na thread do servidor, evitando conflitos
    nick = input("Olá, qual é o seu nome? ")  # Nick do peer
    host = input(f'Qual é o seu ip, {nick}? ')  # Ip do peer
    firstEntry = True  # Variável utilizada para criar o servidor apenas na primeira iteração, pois ao abrir outro servidor com a mesma porta um erro é gerado
    cmd = ''
    while cmd != '3':
        cmd = input(
            "\nBem-vindo ao nosso app de mensagem, digite: \n1 - Se deseja criar uma sala\n2 - Se deseja se conectar a "
            "uma sala\n3 - Para sair\n")
        if cmd == '1':  # Criar sala
            roomName = input('Qual será o nome da sala? ')
            port = int(input('Insira sua porta: '))
            room = Room(roomName, nick, host, port)
            adm = True
            client = Client(nick, host, port, adm, room, host, port)  # Cliente é uma classe normal
            if firstEntry:
                server = Server(nick, host, port, room, client, lock)  # Server é uma thread
                server.start()
                firstEntry = False
            else:              
                if server.port != port:  # Se existia um server com porta diferente para este peer, ele é finalizado e um novo é aberto.
                    server.running = False
                    server = Server(nick, host, port, room, client, lock)
                    server.start()
                else:  # Se a porta for a mesma, o server á apenas atualizado com as novas informações
                    server.port = port
                    server.room = room
                    server.myClient = client
             

            print(f'Sua sala foi criada no endereço {host} e porta {port}!!')
            time.sleep(0.03)
            chekingMembers = CheckMembers(room, client)  # Nesta thread, o adm checa continuamente se algum membro foi desconectado
            chekingMembers.start()
            client.chatPeer()

        elif cmd == '2':
            roomIP = input('Qual é o IP da sala? ')  # Ip do adm da sala
            roomPort = int(input('Qual é a porta da sala? '))  # Porta do adm da sala
            try:  # Se o usuário inserir um endereço de sala (ip, porta) inexistente, um erro é gerado no socket, logo, o try é necessário
                socket_ = socket(AF_INET, SOCK_STREAM)
                socket_.connect((roomIP, roomPort))

                socket_.sendall(
                    f'{nick}\nrequest\n'.encode())  # Envia 'request' e nick para indicar que o peer quer fazer uma requisição para entrar na sala
                print('Conectando...')

                answer = splitMessage(str(socket_.recv(1024), 'UTF-8'))  # Resposta do servidor, se foi aceito ou não na sala
                if answer[0] == 'Voce foi aceito na sala':
                    print('Você entrou na sala!!')
                    # Todas as informações a seguir são da sala, enviadas pelo adm
                    roomName, port, nickADM, ipADM, portADM = answer[1], int(answer[2]), answer[3], answer[4], int(answer[5])
                    print('-' * 40 + '\n' + f'Bem-vindo à sala {roomName}\n' + '-' * 40)

                    nextIndex = 6  # Indice da próxima informação na lista de resposta. Varia de acordo com o tamanho de cada dicionário e lista

                    queueADM = []
                    qntQueueADM = int(answer[nextIndex])
                    nextIndex += 1
                    for i in range(qntQueueADM):
                        queueADM.append(answer[nextIndex])
                        nextIndex += 1
                    queueADM.append(nick)

                    members = {}
                    qntMembers = int(answer[nextIndex])
                    nextIndex += 1
                    for i in range(qntMembers):
                        members[answer[nextIndex]] = (answer[nextIndex+1], int(answer[nextIndex+2]))
                        nextIndex += 3
                    members[nick] = (host, port)

                    ips = {}
                    qntIps = int(answer[nextIndex])
                    nextIndex += 1
                    for i in range(qntIps):
                        ips[(answer[nextIndex], int(answer[nextIndex+1]))] = answer[nextIndex+2]
                        nextIndex += 3
                    ips[(host, port)] = nick

                    ban = []
                    qntBans = int(answer[nextIndex])
                    nextIndex += 1
                    for i in range(qntBans):
                        ban.append((answer[nextIndex], answer[nextIndex+1]))
                        nextIndex += 2


                    room = Room(roomName, nickADM, ipADM, portADM, queueADM, members, ips,
                                ban)  # Cria um objeto Room com os dados recebidos pelo adm da sala
                    adm = False
                    client = Client(nick, host, port, adm, room, roomIP, roomPort)  # Inicializa sua classe cliente com seus dados e a Room criada
                    if firstEntry:
                        server = Server(nick, host, port, room, client, lock)  # Inicializa a thread server
                        server.start()
                        firstEntry = False
                    else:     
                        if server.port != port:  # Se existia um server com porta diferente para este peer, ele é finalizado e um novo é aberto.
                            server.running = False
                            server = Server(nick, host, port, room, client, lock)
                            server.start()
                        else:  # Se a porta for a mesma, o server á apenas atualizado com as novas informações
                            server.port = port
                            server.room = room
                            server.myClient = client


                    chekingADM = CheckADM(room, nick, client)  # Todos os usuários da sala checam continuamente se o adm não se desconectou de forma inesperada
                    chekingADM.start()
                    # A partir deste ponto o usuário já pode interagir com o chat
                    client.chatPeer()
                    # A partir deste ponto, o usuário saiu ou foi removido da sala
                    client.running = False


                else:  # Nesta condição, o usuário não entrou na sala, e a mensagem que será printada informará ao usuário o porquê
                    print(answer[0])
            except:                
                print('Sala não encontrada')
        elif cmd == '3':
            try:  # Caso tenha um servidor, irá pará-lo
                server.running = False
            except:
                pass
        else:
            print('Comando inválido\n')







lock = threading.Lock()
if __name__ == "__main__":
    startPeer()
