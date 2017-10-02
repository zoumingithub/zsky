使用说明

>安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问 http://IP 

>后台地址 http://IP/admin 

程序默认数据库密码123456

修改simdht_worker.py里的max_node_qsize的大小调节爬取速度（队列大小）

执行  python manage.py init_db     创建表/平滑升级表结构

执行  python manage.py create_user  创建管理员

执行  python manage.py changepassword  修改管理员密码

执行  systemctl start gunicorn  启动网站

执行  systemctl start mariadb  启动数据库

执行  systemctl status mariadb  查看数据库运行状态

执行  systemctl restart mariadb  重新启动数据库

执行  systemctl status gunicorn  查看gunicorn运行状态

执行  systemctl restart gunicorn   重新启动网站

执行  systemctl restart indexer  手动重新索引

执行  systemctl start searchd  开启搜索进程

执行  systemctl status searchd  查看搜索进程运行状态

执行  systemctl restart searchd   重新启动搜索进程

**Q：如何实现远程主机反向代理本程序？**

A：

修改本机的/etc/systemd/system/gunicorn.service其中的127.0.0.1:8000修改为0.0.0.0:8000然后执行systemctl daemon-reload

本程序所在主机不开启nginx，远程主机开启nginx，配置反向代理，绑定域名，配置文件参考程序内的nginx.conf ，即可使用域名正常访问。

**Q：如何限制/提高爬取速度？**

A：修改simdht_worker.py里的max_node_qsize=后面的数字，越大爬取越快，越小爬取越慢

**Q：如何修改数据库密码？**

A：执行mysqladmin -uroot -p password 123456!@#$%^                     //将提示输入当前密码，123456!@#$%^是新密码

**Q：修改数据库密码后怎么修改程序里的配置？**

A：修改manage.py里的mysql+pymysql://root:密码@127.0.0.1、修改manage.py里的DB_PASS、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass

**Q：怎么确定爬虫是在正常运行？**

A：执行 ps -ef|grep -v grep|grep simdht 如果有结果说明爬虫正在运行

**Q：更新manage.py/模板后怎么立即生效？**

A：执行 systemctl restart gunicorn 重启gunicorn

**Q：为什么首页统计的数据远远小于后台的数据？**

A：在数据量变大后，索引将占用CPU 100%，非常影响用户访问网站，为了最小程度减小此影响 默认设置为每天早上5点更新索引，你想现在更新爬取结果的话，手动执行索引 systemctl restart indexer ，需要注意的是，数据量越大 索引所耗费时间越长

**Q：如何查看索引是否成功？**

A：执行 systemctl status indexer 可以看到索引记录

**Q：觉得索引速度慢，如何加快？**

A：修改sphinx.conf里面的mem_limit = 512M ，根据你的主机的内存使用情况来修改，越大索引越快，最大可以设置2048M

**Q：如何确定搜索进程是否正常运行**

A：执行 systemctl status searchd ，如果是绿色的running说明搜索进程完全正常

**Q：如何备份数据库？**

A：执行 mysqldump -uroot -p zsky>/root/zsky.sql  导出数据库              //将提示输入当前密码，数据库导出后存在/root/zsky.sql

**Q：数据库备份后，现在重新安装了程序，如何导入旧数据？**

A：执行 mysql -uroot -p zsky</root/zsky.sql                     //假设你的旧数据库文件是/root/zsky.sql，将提示输入当前密码，输入后耐心等待

**Q：如何迁移到新主机？**

A：备份数据库（方法见上面）→ 程序拷贝到新主机 → 安装程序 → 导入数据库（方法见上面）→ 重新索引

**更多疑问？请[加群](http://shang.qq.com/wpa/qunwpa?idkey=d119da6023cc49729a61139ca4b8bb0ee770d8d9a89383939c4a45159f82bc6d)**

**Q：我以前使用的搜片大师/手撕包菜，可以迁移过来吗？**

A：程序在开发之初就已经考虑到从这些程序迁移过来的问题，所以你不用担心，完全可以无缝迁移。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**Q：网站经常收到版权投诉，有没有好的解决办法？**

A：除了删除投诉的影片数据外，你可以使用前端Nginx、后端gunicorn+爬虫+数据库+索引在不同主机上的模式，甚至多前端模式，这样 即使前端被主机商强行封机，也能保证后端数据的安全。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**郑重申明:**

若你从其他地方获取到源码，再联系我咨询程序的使用，将按500元/次收费！


