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
        cred=HTTPBasicAuth(ruser,rpass);
        r = requests.get(rurl, auth=cred)
        if r.status_code != 200:
            return("ERROR, Cannot connect to Rancher")
        js = r.json()

        if len(args) == 0 or args[0] in {"--help", "-h", "help"}:
            output = "usage: \n"
            output += "!rancher status|ops (serviceName)\n"
            output += "!rancher upgrade|update serviceName\n"
            output += "!rancher ok|finish|confirm|finishupgrade|complete serviceName\n"
            output += "!rancher abort|revert|rollback|cancel serviceName\n"
            output += "!rancher scale serviceName scaleNumber\n"
            return(output)

        elif args[0] in {"status", "ops"}:
            output  = "name|status|state|scale\n"
            output += "----|------|-----|-----\n"
            unhealthy=""
            for foo in js['data']:
                if len(args) == 2:
                    if args[1] != foo['name']:
                        continue
                text = foo['name']+ "|" +foo['healthState']+ "|" +foo['state']+ "|" +str(foo['scale'])+"\n"
                if foo['healthState'] != "healthy":
                    unhealthy += text
                else:
                    output += text
            output += unhealthy 
            return(output)

        else:
            if len(args) < 2:
                return "Usage: "+args[0]+" serviceName"
            else:
                serviceName = args[1]
                for foo in js['data']: 
                    if foo['name'] == serviceName:
                        serviceData = foo
                        break;
            if args[0] in {"upgrade", "update", "up"}:
                actUrl=serviceData['actions']['upgrade']
                upgrade=serviceData['upgrade']
                r = requests.post(actUrl, json=upgrade, auth=cred)
            elif args[0] in {"ok", "finish", "finishupgrade", "confirm", "complete"}:
                actUrl=serviceData['actions']['finishupgrade']
                r = requests.post(actUrl, auth=cred);
            elif args[0] in {"abort", "revert", "rollback", "cancel"}:
                actUrl=serviceData['actions']['rollback']
                r = requests.post(actUrl, auth=cred);
            elif args[0] == "scale":
                try:
                    newscale=int(args[2])
                    actUrl=serviceData['links']['self']
                    serviceData['scale']=newscale
                    r = requests.put(actUrl, json=serviceData, auth=cred)
                except ValueError:
                    return "Need to set a scale number boss..."
            if r.status_code in { 202, 200 }:
                return("You got it boss.")
            else:
                return(args[0] + " failed boss (" +str(r.status.code)+ ")")

