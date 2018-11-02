import logging
# these are parameters to configure the distributor
availableSessions = ['QemuSession','PandaSession']
sessionType = availableSessions[1]

numberOfMachinesToStartWith = 1
maxAllowedNumberOfMachnes = 1
loggingLevel = logging.DEBUG
delayAfterStartOfGenode = 60
timesTasksetIsTriedBeforeLabeldBad = 2
genodeTimeout = 60


taskTypes = ['hey'] # to use all available task types use the following list instead:['hey', 'pi', 'tumatmul', 'cond_mod', 'cond_42']

tasksPerLine = 100 # number of tasks put in one list
linesPerCall = 6 # lines per file written in one execution

taskParameters = {	'PKG':
						{1:'hey',
						 2:'pi',
						 3:'tumatmul',
						 4:'cond_mod'#,
						 #5:'cond_42'
						},
				'ARG':
						{'hey':(0,1),#23-28
						'pi':(13,21),#84-1600
						'tumatmul':(12,19),#104-2700
						'cond_mod':(25,30),#130-3000
						'cond_42':(2,4)
						},
				'PRIORITY': (1,127), # think we can put constraint on this and just provide maybe 5 different values, so values appear more often and in the end with fp scheduling only the difference should matter(?)
				'PERIOD': (1,8),
				'OFFSET': (0,1),
				'NUMBEROFJOBS': (1,10),
				'QUOTA': (100, 100), #(1, 100),# we could just assign arbitrary big values to this and to caps as well, cause a working task, which is the assumption for an initial taskset, would have good values for that and both (caps and ram) are available in abundance 
				'CAPS': (235, 235) #(10, 235)
				}