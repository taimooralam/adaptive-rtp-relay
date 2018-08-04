## Introduction
Adaptive bitrate streaming is a technique commonly deployed in HTTP-based streaming to make it more flexible in different network and receiver conditions. The technique combined with mainly distributed HTTP network has gained popularity so that it has pushed RTP out of the streaming market. The underlying idea behind the adaptive feature of streaming is adjusting the transmission to the instantaneous network and receiver conditions seamlessly by changing sender parameters. 

While different implementations are deployed in the Internet, MPEG-DASH gave rise to the technique among others. Adaptive RTP, which is attempted few times, does not draw the same attention as the DASH. While a reason for that is the considerable prevalence of HTTP, the other is the poor performance of the implementations.

## Motivation
In the project, we aim at the question whether there is any advantage of making RTP adaptive. With the adaptive feature, we think that receivers would have seamless streaming experience without any further manual control.

## Design
The project is divided into two distinct and independent stages. At the first stage, which is relatively easy, a multiplexing scheme for the RTP sender is implemented. At this stage, the sender starts to transmit different video files (which modelled to be different qualities for the adaptation) to different
receivers simultaneously. 

In the second stage, where adaptation comes into the stage, sender dynamically determines the video files to send to the receivers by observing the feedback. The difference between the first and the second stages is in the second stage, video file and receiver pairs are not hard coded and fixed in advance but dynamically matched during the operation by the sender. By exploiting the RTP and especially RTCP feedback, streaming becomes adaptive.

## Implementation
### Introduction
The implementation consists of 2 stages. In the first stage, the relay multiplexes the incoming RTP streams (same video file with different qualities) to the receiver based on a hard coded, predetermined value. In the second stage, the toggle value that determines the outgoing stream become dynamic. Finally, as the third stage which was not expected in the design, an RTCP generator for testing and evaluation is implemented.

In the first stage, a python code which acts as a multiplexer is applied. Multiplexer listens to the two
VLC RTP senders. Then, based on the hard coded toggle value, which is either zero or one, sends one of the incoming streams to the receiver VLC player. 

In the second stage, we developed an interpreter module which determines the toggle value. This module, the Interpreter, takes RTCP Receiver Reports [1] as the input and based on its Delay Field, determines the outgoing stream. The details of the final implementation are given in the figure below.

### The Relay and Designing the Flow of Data
The relay is the python program that is signified with the large central rectangle. This program takes two streams, high and low quality respectively. Two processes run within the relay which listens to these streams respectively. Then these processes are connected via pipes to a central toggle process that switches streams and sends them to the end point VLC player.

Pipes were a design choice here. An earlier prototype was built using shared memory, but that generated problems since there was additional overload in checking whether the buffer data in shared memory was already sent out to the client or not. Pipes were then a sensible choice because they are programmatically blocking. That means the sender process will block until it receives the next data buffer from the receiver processes. It guarantees that RTP is not sent twice to the receiver processes.

### Fixing Sequence Numbers
Another challenge that we faced in implementing this was the inconsistent sequence numbers when the streams switched from low to high or vice versa. It was solved by parsing the received packets and changing their sequence numbers when being sent to the receiver process.

The streams were toggled in the Sender process Based on Toggle Value (SPBTV) process (the inner rectangle within the large relay rectangle). The toggle value was a shared memory available to all processes in the relay that was read and write protected using mutexes. This toggle value determined whether the SPBTV process sends the high or the low-quality stream to the output source. 

### The Receiver Report Challenge and the Packet Sniffer
One of the biggest challenges faced was the receiver VLC did not generate RTCP Receiver Reports which was the core thesis of our project. This problem mandated that another the Python program called sniffer.py be developed that would
sniff the incoming RTP traffic to the receiver VLC, detect the network quality and send RTCP Receiver Reports based on these values.

The bottom rectangle in the figure below shows this program that is run the same machine as the receiver VLC program. The sniffer must use RAW sockets because the RTP port is already bound to the receiver VLC program. The RAW packets had to be additionally parsed because they included IP and UDP headers. After getting to the  or process through a pipe. The RTCP generator process had a scheduler thread which waited for a configurable period and then generated an RTCP Receiver Report based on the data received from the RTP packets.

### The Toggling
The sniffer sends the RTCP Receiver Reports back to the relay program. The RTCP interpreter process within the relay program interpreted these values to toggle the multi process - shared toggle value. A value was used to toggle the stream from low to high and high to low. A complete working prototype of this functionality was demonstrated in the lecture.

### Evaluation 
After implementing the Adaptive RTP Relay, VLC Media player is chosen as part of the test case. However, later it was noticed that VLC Media Player does not provide RTCP Receiver Report which is the input of the Interpreter in the Relay. Upon this news, another module which sniffs the RTP traffic and generates RTCP packets has to be implemented as well. To underline that, this module is not part of the relay but needed for the evaluation. The test case of this implementation consists of 3 VLC Media Players (HQ sender, LQ sender, and
receiver), 2 Python script (Adaptive RTP Relay and RTCP Generator) and 2 Video Files (HQ and LQ). In the test, 2 VLC Media Players streams two video files to the loopback interface and different ports. RTP Relay listens to these ports, receives the streams, determines which one should be forwarded and forwards it to the remaining VLC Media Player. RTCP packet generator sniffs the traffic which is sent from RTP Relay to the receiver VLC Media Player and sends RTCP Receiver
Reports.

As part of the evaluation, first, functionality is tested. It is observed that upon the change in the Delay Field value of the incoming RTCP Receiver Reports, RTP Relay toggles the value which affects the forwarded traffic. It worked successfully without any integration problem. Later, the response time is also considered. Here, the toggle value is printed out to the terminal and observed that it toggles successfully upon every incoming RTCP Receiver Report correctly. Finally, the response time of VLC Media Player is checked. It is noted that VLC Media Player changes the quality of shown video successfully after few seconds. The reason for this amount of response time is the buffering of the stream. Before the switch, some portions of the stream has to be buffered at the Media Player side.

## Organizational
Mr Kirdan contributed to the design, the first stage of implementation, testing, evaluation and reporting. In the design phase, he worked with determining use cases and defining the scope of the project. In the implementation, he contributed to the RTP relay and multiplexer. In testing and evaluation, he determined the test cases and the evaluation of the implementation. Finally, he also contributed to the reporting. In the end, he was delighted and happy with his team partner both performance and motivation and thinking that workload distributed equally and justly. Mr Alam contributed to the major stage of implementation of the relay and sniffer. He was responsible for designing, implementing and the testing of the internals of relay program. He also parsed and changed the sequence numbers of the incoming RTP packets on the relay side.

Furthermore, he contributed to the sniffer program, where the additional parsing of the RAW socket was necessary to reach the RTP packet header on the receiver VLC machine. He also contributed to the sending the RTCP receiver reports back to the relay. Mr Alam made a rough draft of the diagram of the implementation and also took part in the documentation of the implementation part in the documentation of the project.

## Conclusion
In a nutshell, the core idea of adaptive RTP relay is designed, implemented, tested and evaluated. As a use case, the multiplexer which transmits different qualities of incoming video files to different receivers is focused. To realise it, a python code which interprets the RTCP feedbacks and determines the outgoing stream adaptively is implemented. To test this implementation, a tester which sniffs RTP and generated RTCP Receiver Reports is also implemented. Based on this test case, the response time of the adaptive feature of RTP streaming is although the relay is highly adaptive, the performance and response time of adaptation is also influenced by the Media Player which was the VLC media player in our test case.

## References
1: RTP: A Transport Protocol for Real-Time Applications. (n.d.). Retrieved July 20, 2017, from
https://tools.ietf.org/html/rfc3550