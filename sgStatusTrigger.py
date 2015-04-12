from datetime import datetime
import os, sys

applicationName = 'api_script'
applicationKey = '0b71a5525895120e4bd3972348e3e2e559a53ec3'
projectFilter = 'ttv_e'
error = []
logPath = 'U:/extensions/studioTools'

print '\n\n', datetime.now()
print '======================================'
print '=    start sgStatusTrigger.py        ='
print '======================================'
print '\n'

# task trigger dependency
taskTriggerDependency = [{'event': {'step': 'ANIMATION', 'task': 'cache', 'status': 'cash'}, 
                        'trigger': {'step': 'LIGHTING', 'task': 'lighting', 'status': 'rdy'}
                        }, 
                        {'event': {'step': 'LIGHTING', 'task': 'lighting', 'status': 'wai'}, 
                        'trigger': {'step': 'COMPOSITING', 'task': 'compositing', 'status': 'rdy'}
                        }]


# version trigger dependency
versionTriggerDependency = [{'event': {'status': 'apr'}, 'trigger': {'status': 'aeo7'}},
                            {'event': {'status': 'vbc'}, 'trigger': {'status': 'reo7'}}]


def registerCallbacks(reg):

    eventFilter = {'Shotgun_Task_Change': ['sg_status_list'], 'Shotgun_Version_Change': ['sg_status_list']}
    reg.registerCallback(applicationName, applicationKey, trigger, eventFilter, None)


def trigger(sg, logger, event, args):
    startTime = datetime.now()
    data = getEventData(sg, event, args)
    printStream(data)

    # check valid project 
    projectName = data['projectName']
    entityType = data['entityType']


    # if there is project data
    if projectName : 
        if projectFilter in projectName : 

            # if type is Task 
            if entityType == 'Task' : 
                taskTrigger(sg, data)

            # if type is Version 
            if entityType == 'Version' : 
                versionTrigger(sg, data)

    else : 
        error.append('No Project name')

    endTime = datetime.now()
    duration = endTime - startTime
    print duration


def taskTrigger(sg, data) : 
    print 'task trigger'

    task = data['entityName']
    taskID = data['entityID']
    status = data['newValue']
    projectName = data['projectName']


    # checking condition
    for eachCondition in taskTriggerDependency : 
        eStep = eachCondition['event']['step']
        eTask = eachCondition['event']['task']
        eStatus = eachCondition['event']['status']

        tStep = eachCondition['trigger']['step']
        tTask = eachCondition['trigger']['task']
        tStatus = eachCondition['trigger']['status']


        # if stream task match the condition
        if task == eTask and status == eStatus : 

            # find shot / step that task has been linked in
            entity = findLinkedAsset(sg, taskID)

            if entity : 

                # find shotID 
                shot = entity['entity']
                shotID = 0

                if shot : 
                    shotID = shot['id']

                # find step (department)
                stepName = str()
                step = entity['step']

                if step : 
                    stepName = step['name']

                if stepName and shotID : 
                    if stepName == eStep : 

                        # find target task that linked in the same shot
                        tTaskEntity = findTriggerTask(sg, shotID, tTask, tStep)

                        # if target task exists 
                        if tTaskEntity : 
                            tTaskID = tTaskEntity['id']

                            # change status
                            result = setTaskStatus(sg, tTaskID, tStatus)

                            if result : 
                                processStatus = 'success'
                                note = 'success'
                                display = '%s %s : %s %s %s -> %s %s %s' % (projectName, processStatus, eStep, eTask, eStatus, tStep, tTask, tStatus)
                                logData = {'project': projectName, 'processStatus': processStatus, 'eStep' : eStep, 'eTask' : eTask, 'eStatus' : eStatus, 'tStep' : tStep, 'tTask' : tTask, 'tStatus' : tStatus, 'display': display}
                                writeLog(logData, 'Task')

                        else : 
                            print 'No task name %s' % tTask
                            note = 'No task found "%s"' % tTask
                            display = '%s %s : %s %s %s -> %s %s %s' % (projectName, processStatus, eStep, eTask, eStatus, tStep, tTask, tStatus)
                            processStatus = 'failed'
                            logData = {'project': projectName, 'processStatus': processStatus, 'eStep' : eStep, 'eTask' : eTask, 'eStatus' : eStatus, 'tStep' : tStep, 'tTask' : '-', 'tStatus' : '-', 'display': display}
                            writeLog(logData, 'Task')

                else : 
                    print 'Step or shotID missing'
                    note = 'Step or shotID missing'
                    display = '%s %s : %s %s %s -> %s %s %s' % (projectName, processStatus, eStep, eTask, eStatus, tStep, tTask, tStatus)
                    processStatus = 'failed'
                    logData = {'project': projectName, 'processStatus': processStatus, 'eStep' : eStep, 'eTask' : eTask, 'eStatus' : eStatus, 'tStep' : tStep, 'tTask' : '-', 'tStatus' : '-', 'display': display}
                    writeLog(logData, 'Task')

            else : 
                error.append('Cannot find linked shot')
                note = 'Cannot find linked shot'
                display = '%s %s : %s %s %s -> %s %s %s' % (projectName, processStatus, eStep, eTask, eStatus, tStep, tTask, tStatus)
                processStatus = 'failed'
                logData = {'project': projectName, 'processStatus': processStatus, 'eStep' : eStep, 'eTask' : eTask, 'eStatus' : eStatus, 'tStep' : tStep, 'tTask' : '-', 'tStatus' : '-', 'display': display}
                writeLog(logData, 'Task')



def versionTrigger(sg, data) : 
    print 'version trigger'

    version = data['entityName']
    versionID = data['entityID']
    versionName = data['entityName']
    status = data['newValue']
    projectName = data['projectName']

    for eachCondition in versionTriggerDependency : 
        eStatus = eachCondition['event']['status']
        tStatus = eachCondition['trigger']['status']

        if status == eStatus : 
            versionTask = findVersionTask(sg, versionID)

            if versionTask : 
                task = versionTask['sg_task']
                project = versionTask['project']
                entity = versionTask['entity']

                if task : 
                    taskID = task['id']
                    taskName = task['name']
                    result = setTaskStatus(sg, taskID, tStatus)

                    if result : 
                        processStatus = 'success'
                        note = ''
                        display = '%s %s : Version %s %s -> Task %s %s' % (projectName, processStatus, versionName, status, taskName, tStatus)
                        logData = {'note': note, 'versionName': versionName, 'status': status, 'taskName': taskName, 'tStatus': tStatus, 'processStatus': processStatus, 'display': display}
                        writeLog(logData, 'Version')

            else : 
                note = 'Error : This version has No task "%s"' % taskName
                processStatus = 'failed'
                display = '%s %s : Version %s %s -> Task %s %s' % (projectName, processStatus, versionName, status, '-', '-')
                logData = {'note': note, 'versionName': versionName, 'status': status, 'taskName': taskName, 'tStatus': tStatus, 'processStatus': processStatus, 'display': display}
                writeLog(logData, 'Version')


def printStream(data) : 
    print '------------------------------'

    for each in data.keys() : 
        print '%s   :  %s' % (each, data[each])

def getEventData(sg, event, args) : 
    # project
    projectName = str()
    projectID = 0

    # entity
    entityName = str()
    entityID = 0

    # meta
    entityType = None
    entityID = None
    oldValue = None
    newValue = None

    # user 
    userID = 0
    userName = str()

    attributeName = event['attribute_name']
    eventType = event['event_type']
    entity = event['entity']
    

    if entity : 
        entityType = entity['type']

        entityID = entity['id']
        entityName = entity['name']

    project = event['project']

    if project : 
        projectID = project['id']
        projectName = project['name']

    meta = event['meta']

    if meta : 
        # task / version
        entityType = meta['entity_type'] 

        # taskID or versionID
        entityID = meta['entity_id']

        oldValue = meta['old_value']
        newValue = meta['new_value']

    user = event['user']

    if user : 
        userID = user['id']
        userName = user['name']

    data = {
            'projectName': projectName,
            'projectID': projectID,
            'entityName': entityName,
            'entityID': entityID,
            'entityType': entityType,
            'oldValue': oldValue,
            'newValue': newValue,
            'userID': userID,
            'userName': userName,
            'attributeName': attributeName,
            'eventType': eventType,
            'entity': entity
            }

    return data



def findLinkedAsset(sg, taskID) : 
    filters = [['id','is', taskID]]
    fields = ['entity', 'step']

    task = sg.find_one('Task',filters = filters, fields = fields)

    return task


def findTriggerTask(sg, shotID, tTaskName, tStep) : 
    filters = [['entity', 'is', {'type': 'Shot', 'id': shotID}], 
                ['content', 'is', tTaskName], 
                ['step.Step.code', 'is', tStep]]

    fields = ['id', 'content']

    task = sg.find_one('Task',filters = filters, fields = fields)

    return task



def findVersionTask(sg, versionID) : 
    filters = [['id', 'is', versionID]]
    fields = ['id', 'sg_task', 'project', 'entity']
    version = sg.find_one('Version', filters = filters, fields = fields)

    return version


def setTaskStatus(sg, taskID, status) : 
    data = { 'sg_status_list': status }
    result = sg.update('Task', taskID, data)

    return result



''' log area ==========================================================================================='''

def writeLog(rawData, entity) : 
    normalLog = getLogPath('normal', entity) 
    dataLog = getLogPath('data', entity)
    logFiles = [normalLog, dataLog]
    logPath = os.path.dirname(normalLog)
    startText = 'Start log'

    if not os.path.exists(logPath) : 
        os.makedirs(logPath)
        
    for logFile in logFiles : 
        if not os.path.exists(logFile) : 
            f = open(logFile, 'w')
            f.write(startText)
            f.close()

    
    timeStr = str(datetime.now()).split(' ')[-1]
    display = rawData['display']
    displayData = '[%s] %s' % (timeStr, display)
    rawData['date'] = timeStr

    appendLog(display, normalLog)
    appendLog(str(rawData), dataLog)

    
 
def appendLog(rawData, filePath) : 

    f = open(filePath, 'a')
    writeData = '\n%s' % rawData
    f.write(writeData)
    f.close()

                

def getLogPath(logType, entity) : 

    scriptLogPath = '%s/logs/sgStatusTrigger' % logPath
    todayDate = str(datetime.now()).split(' ')[0]
    logFile = str()

    if entity == 'Version' : 
        if logType == 'normal' : 
            fileName = '%s_versionLog.txt' % todayDate

        if logType == 'data' : 
            fileName = '%s_versionDataLog.txt' % todayDate

        logFile = '%s/%s' % (scriptLogPath, fileName)



    if entity == 'Task' : 
        if logType == 'normal' : 
            fileName = '%s_taskLog.txt' % todayDate

        if logType == 'data' : 
            fileName = '%s_taskDataLog.txt' % todayDate

        logFile = '%s/%s' % (scriptLogPath, fileName)
    

    return logFile