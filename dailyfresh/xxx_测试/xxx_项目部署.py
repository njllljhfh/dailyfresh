# -*- coding:utf-8 -*-
"""
1.首先客户端请求服务资源，
2.nginx作为直接对外的服务接口,接收到客户端发送过来的http请求,会解包、分析，
3.如果是静态文件请求就根据nginx配置的静态文件目录，返回请求的资源，
4.如果是动态的请求,nginx就通过配置文件,将请求传递给uWSGI；uWSGI 将接收到的包进行处理，并转发给wsgi，
5.wsgi根据请求调用django工程的某个文件或函数，处理完后django将返回值交给wsgi，
6.wsgi将返回值进行打包，转发给uWSGI，
7.uWSGI接收后转发给nginx,nginx最终将返回值返回给客户端(如浏览器)。
8.*注:不同的组件之间传递信息涉及到数据格式和协议的转换

作用:
1. 第一级的nginx并不是必须的，uwsgi完全可以完成整个的和浏览器交互的流程；
2. 在nginx上加上安全性或其他的限制，可以达到保护程序的作用；
3. uWSGI本身是内网接口，开启多个work和processes可能也不够用，而nginx可以代理多台uWSGI完成uWSGI的负载均衡；
4. django在debug=False下对静态文件的处理能力不是很好，而用nginx来处理更加高效。
"""

"""
区分几个概念:
要注意 WSGI / uwsgi / uWSGI 这三个概念的区分

WSGI：
全称是Web Server Gateway Interface（web服务器网关接口）
WSGI是一种通信协议，一种规范，它是web服务器和web应用程序之间的接口
它的作用就像是桥梁，连接在web服务器和web应用框架之间
没有官方的实现，更像一个协议。只要遵照这些协议，WSGI应用(Application)都可以在任何服务器(Server)上运行

uwsgi：
是一种传输协议，用于定义传输信息的类型。常用于在uWSGI服务器与其他网络服务器的数据通信

uWSGI：
uWSGI是一个Web服务器，它实现了WSGI协议、uwsgi协议、http协议 等协议
uWSGI代码完全用C编写，效率高、性能稳定

提示
如果某台服务器实现了uwsgi协议，那么它就可以运行遵守了WSGI协议的WEB程序，比如Django程序
"""