from server import *
from room import *
from client import *
import time

def startPeer():
    global lock  # Variavel utilizada para processar separadamente os pedidos na thread do servidor, evitando conflitos
    nick = input("Qual o seu nome? ")  # Nick do peer
    host = input(f'Qual o seu ip, {nick}? ')  # Ip do peer
    port = int(input('Qual a sua porta? '))  # Porta do peer
    firstEntry = True  # Variavel utilizada para criar o servidor apenas na primeira iteracao, pois ao abrir outro servidor com a mesma porta um erro e gerado
    cmd = ''
    roomsBanned = []  # Lista de salas em que o cliente foi banido, evitando requests desnecessarios
    while cmd != '3':
        cmd = input(
            "\nBem-vindo ao nosso app de mensagem, digite: \n1 - Se deseja criar uma sala\n2 - Se deseja se conectar a "
            "uma sala\n3 - Para sair\n")
        if cmd == '1':  # Criar sala
            roomName = input('Qual sera o nome da sala? ')
            room = Room(roomName, nick, host, port)
            adm = True
            client = Client(nick, host, port, adm, room)  # Cliente e uma classe normal
            if firstEntry:
                server = Server(nick, host, port, room, client, lock)  # Server e uma thread
                server.start()
                firstEntry = False
            else:
                server.myClient = client  # A partir da segunda iteracao no menu, somente o objeto client e a room sao atualizados, ja que o server foi inicializado anteriormente
                server.room = room

            print(f'Sua sala foi criada no endereco {host} e porta {port}!!')
            time.sleep(0.03)
            chekingMembers = CheckMembers(room, client)  # Nesta thread, o adm checa continuamente se algum membro foi desconectado
            chekingMembers.start()
            client.chatPeer()

        elif cmd == '2':
            roomIP = input('Qual e o IP da sala? ')  # Ip do adm da sala
            roomPort = int(input('Qual e a porta da sala? '))  # Porta do adm da sala
            if (roomIP, roomPort) in roomsBanned:
                print('Voce esta banido desta sala!')
            else:
                try:  # Se o usuario inserir um endereco de sala (ip, porta) inexistente, um erro e gerado no socket, logo, o try e necessario
                    socket_ = socket(AF_INET, SOCK_STREAM)
                    socket_.connect((roomIP, roomPort))
                    socket_.sendall(str(int(port)).encode())  # Envia sua porta para ser cadastrada caso o peer seja aceito na sala
                    time.sleep(0.1)

                    socket_.sendall(
                        ('request\n' + nick + '\n').encode())  # Envia 'request' e nick para indicar que o peer quer fazer uma requisicao para entrar na sala
                    print('Conectando...')

                    answer = splitMessage(str(socket_.recv(1024), 'UTF-8'))  # Resposta do servidor, se foi aceito ou nao na sala                    
                    if answer[0] == 'Voce foi aceito na sala':
                        print('Voce entrou na sala!!')
                        # Todas as informacoes a seguir sao da sala, enviadas pelo adm
                        roomName, nickADM, ipADM, portADM = answer[1], answer[2], answer[3], int(answer[4])
                        print('-' * 40 + '\n' + f'Bem-vindo a sala {roomName}\n' + '-' * 40)

                        nextIndex = 5  # Indice da proxima informacao na lista de resposta. Varia de acordo com o tamanho de cada dicionario e lista

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
                            ban.append((answer[nextIndex], int(answer[nextIndex+1])))
                            nextIndex += 2

                        print(queueADM, members, ips, ban)
                        room = Room(roomName, nickADM, ipADM, portADM, queueADM, members, ips,
                                    ban)  # Cria um objeto Room com os dados recebidos pelo adm da sala
                        adm = False
                        client = Client(nick, host, port, adm, room)  # Inicializa sua classe cliente com seus dados e a Room criada
                        if firstEntry:
                            server = Server(nick, host, port, room, client, lock)  # Inicializa a thread server
                            server.start()
                            firstEntry = False
                        else:
                            server.room = room
                            server.myClient = client

                        chekingADM = CheckADM(room, nick, client)  # Todos os usuarios da sala checam continuamente se o adm nao se desconectou de forma inesperada
                        chekingADM.start()
                        # A partir deste ponto o usuario ja pode interagir com o chat
                        client.chatPeer()
                        # A partir deste ponto, o usuario saiu ou foi removido da sala
                        client.running = False
                        if client.banned:
                            roomsBanned.append((roomIP, roomPort))


                    elif answer[0] == 'Recusada, o ADM nao permitiu a sua entrada':
                        print(answer)
                    else:  # Nesta condicao, o adm da sala recusou e baniu o usuario de entrar na sala
                        roomsBanned.append((roomIP, roomPort))
                        print(answer)
                except:
                    print('Sala nao encontrada')
        elif cmd == '3':
            pass
        else:
            print('Comando invalido\n')







lock = threading.Lock()
if __name__ == "__main__":
    startPeer()
