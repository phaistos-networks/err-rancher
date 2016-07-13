from errbot import BotPlugin, botcmd, webhook
import requests
import os
from requests.auth import HTTPBasicAuth

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
            output += "!rancher upgrade|update serviceName\n"
            output += "!rancher ok|finish|confirm|finishupgrade|complete serviceName\n"
            output += "!rancher abort|revert|rollback|cancel serviceName\n"
            output += "!rancher scale serviceName scaleNumber\n"
            return(output)

        r = requests.get(rurl+"/v1", auth=basic)
        if r.status_code != 200:
            return("ERROR, Cannot connect to Rancher")
        js = r.json()

        if args[0] in {"status", "ops"}:
            projects = requests.get(js['links']['projects'], auth=basic).json()
            output  = "env|name|status|state|scale\n"
            output += "---|----|------|-----|-----\n"
            for project in projects['data']:
                unhealthy=""
                if project['state'] != "inactive":
                    services = requests.get(project['links']['services'], auth=basic).json()
                    for service in services['data']:
                        if len(args) == 2:
                            if args[1] != service['name']:
                                continue
                        text = project['name']+ "|" +service['name']+ "|" +service['healthState']+ "|" +service['state']+ "|" +str(service['scale'])+"\n"
                        if service['healthState'] != "healthy":
                            unhealthy += text
                        else:
                            output += text
                    output += unhealthy
                else:
                    output += project['name'] +"|-|inactive|-|-\n"
            return(output)

        else:
            if len(args) < 3:
                return "Usage: "+args[0]+" service env"
            else:
                serviceName = args[1].lower()
                serviceEnv = args[2].lower()
                serviceFound = 0
                projects = requests.get(js['links']['projects'], auth=basic).json()
                for project in projects['data']:
                    if project['name'].lower() == serviceEnv:
                        services = requests.get(project['links']['services'], auth=basic).json()
                        for service in services['data']:
                            if service['name'].lower() == serviceName:
                                serviceData = service;
                                serviceFound = 1;
                                break;
                        break;
            if serviceFound == 0:
                return "No service "+args[0]+" found in "+args[1]

            if args[0] in {"upgrade", "update", "up"}:
                if 'upgrade' not in serviceData['actions']:
                    return "Action upgrade not available for "+args[1]+ " in " +args[2]
                actUrl=serviceData['actions']['upgrade']
                upgrade=serviceData['upgrade']
                r = requests.post(actUrl, json=upgrade, auth=basic)
            elif args[0] in {"ok", "finish", "finishupgrade", "confirm", "complete"}:
                if 'finishupgrade' not in serviceData['actions']:
                    return "Action finishupgrade not available for "+args[1]+ " in " +args[2]
                actUrl=serviceData['actions']['finishupgrade']
                r = requests.post(actUrl, auth=basic);
            elif args[0] in {"abort", "revert", "rollback", "cancel"}:
                if 'rollback' not in serviceData['actions']:
                    return "Action rollback not available for "+args[1]+ " in " +args[2]
                actUrl=serviceData['actions']['rollback']
                r = requests.post(actUrl, auth=basic);
            elif args[0] == "scale":
                try:
                    newscale=int(args[3])
                    if newscale < 1:
                        return "Sorry boss, got to be at least 1"
                    actUrl=serviceData['links']['self']
                    serviceData['scale']=newscale
                    r = requests.put(actUrl, json=serviceData, auth=basic)
                except (IndexError, ValueError):
                    return "Need to set a (valid) scale number boss..."
            if r.status_code in { 202, 200 }:
                return("You got it boss.")
            else:
                return(args[0] + " failed boss (" +str(r.status.code)+ ")")

