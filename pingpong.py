from table import Table, LogEntry, RacketData, BallData, CardData, DIM, TMAX, PL, RS
from table import ROUND_NUMBER, print_none, my_print
import shelve


def race(round_count,
         west_name, west_serve, west_play, west_summarize,
         east_name, east_serve, east_play, east_summarize):
    # 生成球桌
    main_table = Table()
    main_table.players['West'].bind_play(west_name, west_serve, west_play, west_summarize)
    main_table.players['East'].bind_play(east_name, east_serve, east_play, east_summarize)
    log = list()

    # 读取历史数据，文件名为"DS-<name>"
    for side in ('West', 'East'):
        d = shelve.open('DS-%s' % (main_table.players[side].name,))
        try:
            ds = d['datastore']
        except KeyError:  # 如果这个文件没有内容，说明球队尚未建立历史数据
            ds = dict()
        finally:
            d.close()
        main_table.players[side].set_datastore(ds)

    # 发球
    main_table.serve()

    # 开始打球
    while not main_table.finished:
        # 记录日志项
        log.append(LogEntry(main_table.tick,
                            RacketData(main_table.players[main_table.side]),
                            RacketData(main_table.players[main_table.op_side]),
                            BallData(main_table.ball),
                            CardData(main_table.card_tick, main_table.cards, main_table.active_card)))
        # 运行一趟
        main_table.time_run()

    # 记录最后的回合
    log.append(LogEntry(main_table.tick,
                        RacketData(main_table.players[main_table.side]),
                        RacketData(main_table.players[main_table.op_side]),
                        BallData(main_table.ball),
                        CardData(main_table.card_tick, main_table.cards, main_table.active_card)))

    # 终局，让双方进行本局总结
    main_table.postcare()

    # 最后，保存双方的历史数据，文件名为"DS-<name>"
    for side in ('West', 'East'):
        d = shelve.open('DS-%s' % (main_table.players[side].name,))
        d['datastore'] = main_table.players[side].datastore
        d.close()

    # 终局，保存复盘资料，文件名称记录了胜负及原因，对战双方名称，和选边
    shelve_name = '[%s.%s]%s-VS-%s-%03d' % (PL[main_table.winner],
                                              RS[main_table.reason],
                                              west_name, east_name,
                                              round_count)
    d = shelve.open(shelve_name)
    d['DIM'] = DIM
    d['TMAX'] = TMAX
    d['tick_step'] = main_table.tick_step
    d['West'] = west_name
    d['East'] = east_name
    d['tick_total'] = main_table.tick
    d['winner'] = main_table.winner
    d['winner_life'] = main_table.players[main_table.winner].life
    d['reason'] = main_table.reason
    d['log'] = log
    d.close()
         
    # 终局，生成一个bat文件，双击即可直接运行show.py，免除了找半天的痛苦
    with open(shelve_name + '.bat', 'w') as bat:
        bat.write('python show.py %s'%(shelve_name))

    # 终局打印信息输出
    my_print("%03d) %s win! for %s, West:%s(%d）, East:%s(%d),总时间: %d ticks %.3fs:%.3fs" %
             (round_count, main_table.winner, main_table.reason,
              west_name, main_table.players['West'].life,
              east_name, main_table.players['East'].life, main_table.tick,
              main_table.players['West'].clock_time,
              main_table.players['East'].clock_time))


import os

# 取得所有以T_开始文件名的算法文件名
players = [f[:-3] for f in os.listdir('.') if os.path.isfile(f) and f[-3:] == '.py' and f[:2] == 'T_']
i = 0
for west_name in players:
    for east_name in players:
        if west_name != east_name:
            my_print('----------------------%s vs %s-------------------------' % (west_name, east_name))
            exec('import %s as WP' % (west_name,))
            exec('import %s as EP' % (east_name,))
            for i in range(ROUND_NUMBER):
                race(i, west_name, WP.serve, WP.play, WP.summarize, east_name, EP.serve, EP.play, EP.summarize)
