from errbot import BotPlugin, botcmd, webhook
import requests
import os
from requests.auth import HTTPBasicAuth
from time import sleep, time

class Rancher(BotPlugin):
    """Rancher Module. Set RANCHER_URL, RANCHER_USER and RANCHER_PASS as env variables"""

    @botcmd(split_args_with=None)
    def rancher(self, msg, args):
        """use help to see available options"""
        ruser=os.getenv('RANCHER_USER', "asd123")
        rpass=os.getenv('RANCHER_PASS', "asd123")
        rurl=os.getenv("RANCHER_URL", "http://localhost:8080")
        basic=HTTPBasicAuth(ruser,rpass);

        if len(args) == 0 or args[0] in {"--help", "-h", "help"}:
            output = "usage: \n"
            output += "!rancher status|ops (serviceName)\n"
            output += "!rancher upgrade|update filter(s)\n"
            output += "!rancher ok|finish|confirm|finishupgrade|complete filter(s)\n"
            output += "!rancher abort|revert|rollback|cancel filter(s)\n"
            output += "!rancher scale filter(s) scaleTo\n"
            output += "!rancher restart filter(s)\n"
            yield(output)
            return

        r = requests.get(rurl+"/v1", auth=basic)
        if r.status_code != 200:
            yield("ERROR, Cannot connect to Rancher")
            return
        js = r.json()

        projects = requests.get(js['links']['projects'], auth=basic).json()
        serviceFound = 0
        output  = "env|name|status|state|scale|alive|total\n"
        output += "---|----|------|-----|-----|-----|-----\n"
        status  = ""

        #Special case. When issuing scale, last arg must be number, not filter.
        if args[0] == "scale":
            try:
                newscale=int(args[len(args)-1])
                if newscale < 1:
                    yield "Sorry boss, got to be at least 1"
                    return
            except (IndexError, ValueError):
                yield "Need to set a (valid) scale number boss..."
                return
            del args[-1]

        for project in projects['data']:
            unhealthy=""
            if project['state'] != "inactive":
                services = requests.get(project['links']['services'], auth=basic).json()
                for service in services['data']:
                    match = True;
                    if len(args) > 1:
                        for i in range(1, len(args)):
                            if args[i].lower() not in service['name'].lower() and args[i].lower() not in project['name'].lower():
                                match = False
                                break
                    if match:
                        serviceData = service
                        serviceFound += 1
                        projectName = project['name']
                        text = projectName + "|" \
                            + service['name'] + "|" \
                            + service['healthState'] + "|" \
                            + service['state'] + "|" \
                            + str(service['scale']) + "|" \
                            + str(service['currentScale']) + "|" \
                            + str(len(service['instanceIds'])) \
                            + "\n"
                        if service['healthState'] != "healthy":
                            unhealthy += text
                        else:
                            status += text
                status += unhealthy
            else:
                status += project['name'] +"|-|inactive|-|-\n"
        if args[0] in {"status", "ops"}:
            output += status;
            yield(output)
            return

        if len(args) < 2:
            yield "Usage: "+args[0]+" filter(s) (newscale)"
            return

        if serviceFound == 0:
            yield "No service matched boss."
            return
        elif serviceFound > 1:
            yield "Matched "+str(serviceFound)+" services. Please add further filters to limit results\n"
            return

        if args[0] in {"upgrade", "update", "up"}:
            if 'upgrade' not in serviceData['actions']:
                yield "Action upgrade not available for "+serviceData['name']
                return
            actUrl=serviceData['actions']['upgrade']
            upgrade=serviceData['upgrade']
            if upgrade == None:
                yield "Sorry, can't help. Please upgrade using web interface this time boss"
                return
            r = requests.post(actUrl, json=upgrade, auth=basic)

        elif args[0] in {"ok", "finish", "finishupgrade", "confirm", "complete"}:
            if 'finishupgrade' not in serviceData['actions']:
                yield "Action finishupgrade not available for "+serviceData['name']
                return
            actUrl=serviceData['actions']['finishupgrade']
            r = requests.post(actUrl, auth=basic);

        elif args[0] in {"abort", "revert", "rollback", "cancel"}:
            if 'rollback' not in serviceData['actions']:
                yield "Action rollback not available for "+serviceData['name']
                return
            actUrl=serviceData['actions']['rollback']
            r = requests.post(actUrl, auth=basic);

        elif args[0] in {"restart"}:
            if 'restart' not in serviceData['actions']:
                yield "Action restart not available for "+serviceData['name']
                return
            actUrl=service['actions']['restart']
            rrs={'rollingRestartStrategy': {}}
            r = requests.post(actUrl, json=rrs, auth=basic)

        elif args[0] == "scale":
            actUrl=serviceData['links']['self']
            serviceData['scale']=newscale
            r = requests.put(actUrl, json=serviceData, auth=basic)

        if r.status_code in { 202, 200 }:
            yield("You got it boss. Performing "+args[0]+" on "+serviceData['name'])
            startTime = time()
            x = 0
            while True:
                x += 1
                sleep(2)
                service = requests.get(serviceData['links']['self'], auth=basic).json()
                if service['state'] in {"upgraded", "active"} and service['healthState'] == "healthy":
                    yield serviceData['name'] +" is ready Boss (time taken: " + str(round(time() - startTime))+ "s)"
                    break
                if (x % 50 == 0):
                    if service['state'] == "upgrading":
                        yield("Upgrading: "+serviceData['name'] +" in progress... (" + str(round(time() - startTime)) + "s)\n")
                    else:
                        yield("It's been a while boss, you'd better check "+serviceData['name']+" out")
                        break
            print(service['currentScale'])
            print(service['instanceIds'])
            print(str(len(service['instanceIds'])))
            output += projectName + "|" \
                + service['name'] + "|" \
                + service['healthState'] + "|" \
                + service['state'] + "|" \
                + str(service['scale']) + "|" \
                + str(service['currentScale']) + "|" \
                + str(len(service['instanceIds'])) \
                + "\n"
            yield(output)
        else:
            yield(args[0] + " failed boss (" +str(r.status_code)+ ") "+r.text)
        return
