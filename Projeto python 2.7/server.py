from socket import *
from client import *
import threading
import time

class Connection(threading.Thread):  # Esta thread representa uma conexão do servidor com apenas um cliente
    def __init__(self, connection, room, senderIP, senderPort, myself, myClient, lock):
        threading.Thread.__init__(self)
        self.connection = connection  # Conexão aberta
        self.room = room  # Sala
        self.lock = lock  # Utilizado para rodar a thread de forma separada das demais, evitando conflito com outras conexões

        self.senderIP = senderIP  # Ip do cliente que abriu a conexão
        self.senderPort = senderPort  # Porta do cliente

        self.myNick = myself[0]  # Nick do peer servidor
        self.myIP = myself[1]  # Ip do peer servidor
        self.myPort = myself[2]  # Porta do peer servidor
        self.myClient = myClient  # Objeto cliente do peer servidor

    def run(self):
        """Recebe os dados de uma conexão com um cliente"""
        try:
            data = self.connection.recv(1024)  # Este dado é referente ao tipo de mensagem que o cliente quer enviar
            if data:
                data = splitMessage(str(data, 'UTF-8'))
                self.lock.acquire()
                if data[0] == 'request':  # Se for um request, ele está querendo entrar na sala
                    adm = (self.room.nickADM == self.myNick and self.room.ipADM == self.myIP and self.room.portADM == self.myPort)
                    if adm:  # Se este servidor for adm da sala
                        nickSender = data[1]  # Nick do cliente
                        print(f'O usuário {nickSender} com ip {self.senderIP} e porta {self.senderPort} está pedindo para entrar na sala'
                        '\nDeseja aceitar a requisição? ')
                        self.myClient.reqEntry = True  # Como o peer servidor está rodando o chat no momento, esta conexão vai requerir a entrada
                        self.myClient.reqMessage = f'O usuário {nickSender} com ip {self.senderIP} e porta {self.senderPort} está pedindo para entrar na sala'
                        '\nDeseja aceitar a requisição? '
                        while self.myClient.reqEntry:  # Neste loop, a thread espera até que a entrada seja inserida dentro do menu da classe cliente do peer servidor
                            pass
                        answer = self.myClient.entry  # A resposta é coletada a partir do atributo entry da classe cliente do peer servidor
                        if answer.lower() in ['y', 'yes', 'sim', 's']:
                            print(f'{nickSender} entrou na sala.')
                            # Envia todas as informações a respeito da sala para o cliente e o insere na sala
                            msgAccepted = 'Voce foi aceito na sala\n'
                            roomName = self.room.roomName + '\n'
                            nickADM = self.room.nickADM + '\n'
                            ipADM = self.room.ipADM + '\n'
                            portADM = str(self.room.portADM) + '\n'

                            lenQueueADM = str(len(self.room.queueADM)) + '\n'
                            queueMembers = ''
                            for member in self.room.queueADM:
                                queueMembers += member + '\n'

                            lenRoomMembers = str(len(self.room.members)) + '\n'
                            roomMembers = ''
                            for member in self.room.members:
                                roomMembers += member + '\n' + self.room.members[member][0] + '\n' + str(self.room.members[member][1]) + '\n'

                            lenIps = str(len(self.room.ips)) + '\n'
                            ipMembers = ''
                            for ip in self.room.ips:
                                ipMembers += ip[0] + '\n' + str(ip[1]) + '\n' + self.room.ips[ip] + '\n'

                            lenBan = str(len(self.room.ban)) + '\n'
                            banMembers = ''
                            for person in self.room.ban:
                                banMembers += person[1] + '\n' + str(person[2]) + '\n'

                            self.connection.sendall((msgAccepted + roomName + nickADM + ipADM + portADM + lenQueueADM + queueMembers
                                                    + lenRoomMembers + roomMembers + lenIps + ipMembers + lenBan + banMembers).encode())
                            time.sleep(0.05)
                            self.myClient.updateRoom('add', nickSender, self.senderIP, self.senderPort)
                            self.room.queueADM.append(nickSender)
                            self.room.ips[(self.senderIP, self.senderPort)] = nickSender
                            self.room.members[nickSender] = (self.senderIP, self.senderPort)

                        else:
                            print(f'Você recusou a entrada do usuário de ip {self.senderIP} e porta {self.senderPort}')
                            print('Deseja bani-lo?')
                            self.myClient.reqEntry = True  # Novamente, o peer servidor solicita dados de entrada da sua classe cliente
                            self.myClient.reqMessage = 'Deseja bani-lo?'
                            while self.myClient.reqEntry == True:
                                pass
                            answer = self.myClient.entry
                            if answer.lower() in ['y', 'yes', 's', 'sim']:
                                self.room.ban.append((self.senderIP, self.senderPort))
                                self.myClient.updateRoom('ban request', nickSender, self.senderIP, self.senderPort)
                                print(f'Você baniu o usuário de ip {self.senderIP} e porta {self.senderPort}')
                                self.connection.sendall('Seu pedido foi recusado e você foi banido'.encode())
                            else:
                                print(f'Você não baniu o usuário de ip {self.senderIP} e porta {self.senderPort}')
                                self.connection.sendall('Recusada, o ADM nao permitiu a sua entrada'.encode())
                    else:
                        self.connection.sendall('Nao sou o adm da sala'.encode())
                elif data[0] == 'text':  # Se for um 'text', basta printar na tela
                    if (self.senderIP, self.senderPort) in self.room.ips:
                        nickSender = self.room.ips[(self.senderIP, self.senderPort)]
                        print(f'{nickSender}: ' + str(data[1]))
                elif data[0] == 'update':  # Se for um update, recebe os dados e atualiza o seu objeto room
                    nick = data[2]
                    ip = data[3]
                    port = int(data[4])
                    if data[1] == 'add':  # Atualiza uma adição de um novo membro
                        if nick != self.myNick:
                            self.room.queueADM.append(nick)
                            self.room.members[nick] = (ip, port)
                            self.room.ips[(ip, port)] = nick
                            print(f'{nick} entrou na sala.')
                    elif data[1] == 'remove':  # Atualiza uma remoção de um membro
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        self.room.queueADM.remove(nick)
                        if nick != self.myNick:
                            print(f'{nick} foi removido da sala.')
                        else:
                            print('Você foi removido da sala.')
                            self.myClient.running = False
                    elif data[1] == 'Disconnected':  # Atualiza uma desconexão de um membro
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        self.room.queueADM.remove(nick)
                        print(f'O usuário {nick} foi desconectado')
                    elif data[1] == 'sair':  # Atualiza uma saída de um membro
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        try:  # Se fosse um adm daria erro, pois adm não fica nesta lista
                            self.room.queueADM.remove(nick)
                        except:
                            pass
                        print(f'{nick} saiu da sala.')
                    elif data[1] == 'ban request':  # Atualiza um banimento de um membro que não estava na sala, ou seja, foi banido pedindo para entrar na sala
                        self.room.ban.append((ip, port))
                    else:  # Atualiza um banimento de um membro que estava na sala
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        self.room.ban.append((ip, port))
                        self.room.queueADM.remove(nick)
                        if nick != self.myNick:
                            print(f'{nick} foi banido da sala.')
                        else:
                            print('Você foi banido da sala!')
                            self.myClient.banned = True
                time.sleep(0.4)
                self.lock.release()
        except:
            pass



class Server(threading.Thread):
    def __init__(self, nick, host, port, room, myClient, lock):
        threading.Thread.__init__(self)
        self.nick = nick
        self.host = host
        self.port = port
        self.room = room
        self.myClient = myClient
        self.lock = lock

    def run(self):
        socket_ = socket(AF_INET, SOCK_STREAM)
        socket_.bind((self.host, self.port))
        socket_.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        socket_.listen(1000)
        while True:
            connection, sender = socket_.accept()
            # print(f'Connected to client {sender}')
            senderIP = sender[0]
            senderPort = int(str(connection.recv(1024), 'UTF-8'))
            if (senderIP, senderPort) not in self.room.ban:
                myself = (self.nick, self.host, self.port)
                threadConnection = Connection(connection, self.room, senderIP, senderPort, myself, self.myClient,
                                              self.lock)
                threadConnection.start()