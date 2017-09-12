使用说明
---
>此一键包只在centos7系统有效
```Bash
yum -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky&&sh zsky.sh
```

>此一键包只在Debian8+系统有效，注意：提示输入数据库密码的时候直接回车
```Bash
apt-get update&&apt-get -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky&&sh zsky_debian.sh
```


>安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问 http://IP 

>后台地址 http://IP/admin 



**Q：如何给首页的推荐影片添加图片、评分？**

A：后台-文件管理-上传图片（图片名不能重复）,后台-首页推荐-新建，
    在“图片”选项中输入/uploads/图片地址 ， 以及片名、评分、显示顺序 , 
    在templates/index.html里调用{{k.pic}}代表图片地址,{{k.score}}代表影片评分



**Q：我以前使用的搜片大师/手撕包菜，可以迁移过来吗？**

A：程序在开发之初就已经考虑到从这些程序迁移过来的问题，所以你不用担心，完全可以无缝迁移。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**Q：网站经常收到版权投诉，有没有好的解决办法？**

A：除了删除投诉的影片数据外，你可以使用前端Nginx、后端gunicorn+爬虫+数据库+索引在不同主机上的模式，甚至多前端模式，这样 即使前端被主机商强行封机，也能保证后端数据的安全。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**郑重申明:**

若你从其他地方获取到源码，再联系我进行程序使用咨询，将按500元/次收费！


