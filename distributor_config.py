import logging
# these are parameters to configure the distributor
availableSessions = ['QemuSession','PandaSession']
sessionType = availableSessions[0]

numberOfMachinesToStartWith = 1
maxAllowedNumberOfMachnes = 1
loggingLevel = logging.DEBUG
delayAfterStartOfGenode = 60
timesTasksetIsTriedBeforeLabeldBad = 2
genodeTimeout = 60


taskTypes = ['hey'] # to use all available task types use the following list instead:['hey', 'pi', 'tumatmul', 'cond_mod', 'cond_42']