#!/usr/bin/env python
#import#
import argparse
#end import#


parser = argparse.ArgumentParser(
    description='Local Memory check for Linux servers. Intended for use on OpsView/Nagios Monitoring systems.', 
    usage = '%(prog)s -n [--hostname] HOSTNAME -w [--warning] warning%% -c [--critical] critical%% -m [--metric] {commit,consumed,swap,hybrid} -v [--verbose] -s [--swap] swap_limit%%', 
    epilog = "Currently a work in progress, please review results before acting on alert, THIS IS NOT MEANT FOR PRODUCTION YET",
    )


### define arguments to be used. secondary metric will be the only non-required metric for now given the progression of the script.
parser.add_argument("-w","--warning", type=int, required=False, default=85, help='Warning alert threshold in percent, defaults to 85')
parser.add_argument("-c","--critical", type=int, required=False, default=95, help='Critical alert thresehold in percent, defaults to 95')
parser.add_argument("-m","--metric", type=str, required=True, choices=('commit','consumed','swap','hybrid'), help='Select alert metric. If Hybrid you should supply \'-s\' otherwise default is 85%%')
parser.add_argument("-v","--verbose",  action='store_true', help='Display more memory stats used in determining alert status.')
parser.add_argument("-s","--swap", type=int, required=False, default=85, help='Value that is only used in Hybrid mode. Percentage of swap used to trigger hybrid alert defaults to 85')



### define argument catchall for future use
args = parser.parse_args()

### Ensure that Critical is greater than Warning
if args.warning > args.critical:
    parser.error("Warning threshold is higher than Critical threshold!")
    
### predefine metrics array
a = {}


meminfo = open('/proc/meminfo','r') # method for grabbing mem info
low_Watermark = int(open('/proc/sys/vm/min_free_kbytes','r').readline().strip()) # grab absolute minimum amount of memory system can run on

try:
    for entry in map( lambda x: x.strip().split( 'kB' )[0].strip(), meminfo.readlines()):
        a[ entry.split( ':' )[0].strip() ] = int( entry.split( ':' )[1].split( 'kB' )[0].strip() )
finally:
    #close files we're working with. Don't trust garbage collectors
    meminfo.close()

### define metrics that aren't available on all systems ###
if 'MemAvailable' in a:                                                                            #define what "memory available" looks like. Older OS's do not calculate this in /proc/meminfo
    memAvail   = a['MemAvailable']                                                                  # But if they do why not use it?
else:
    memAvail   = a['MemFree'] - low_Watermark + (a['Cached'] - min(a['Cached'] / 2, low_Watermark)) #and if they don't then we'll make our own.


### set testing metrics ###
total         = a['MemTotal']                                  # Set memory total
commit        = a['Committed_AS']                              # Define the current system committed memory. This is NOT memory in use, just committed
pressure      = ((commit * 100.0) / total)
ptotal_used   = (100.0 - (memAvail * 100.0 / total) )
pswap         = (100.0 - (a['SwapFree'] * 100.0 / a['SwapTotal']))


### High verbosity output ###
if args.verbose:
    print("Memory Available: " + str(memAvail) + " kb")
    print("Lower Watermark: "  + str(low_Watermark) + " kb")
    print("Total Memory: "     + str(total) + " kb")
    print("Total Commit: "     + str(commit) + " kb")
    print("Total Memory Used: %.2f%%" % ptotal_used)
    print("Swap Used: %.2f%%" % pswap)

### Alert logic based on primary metric. Start with highest check first
if args.metric == "commit":
    if pressure >= args.critical:
       print('CRITICAL - Commit: {0:.2f}'.format(pressure,))
       exit(2)
    elif pressure >= args.warning:
       print('WARNING - Commit: {0:.2f}'.format(pressure,))
       exit(1)
    else:
       print('OK - Commit: {0:.2f}'.format(pressure,))
       exit(0)
elif args.metric == "consumed":
    if ptotal_used >= args.critical:
        print("CRITICAL - UsedMemory: {0:.2f}".format( ptotal_used, ) )
        exit(2)
    elif ptotal_used >= args.warning:
        print("WARNING - UsedMemory: {0:.2f}".format( ptotal_used, ) )
        exit(1)
    else:
        print("OK - UsedMemory: {0:.2f}".format( ptotal_used, ) )
        exit(0)
elif args.metric == "swap":
    if pswap >= args.critical:
        print("CRITICAL - SwapUsed: {0:.2f}".format( pswap, ) )
        exit(2)
    elif pswap >= args.warning:
        print("WARNING - SwapUsed: {0:.2f}".format( pswap, ) )
        exit(1)
    else:
        print("OK - SwapUsed: {0:.2f}".format( pswap, ) )
        exit(0)
elif args.metric == "hybrid":
     if ptotal_used >= args.critical:
          if pswap >= args.swap:
             print("CRITICAL - UsedMemory: {0:.2f} -- UsedSwap: {1:.2f}".format( ptotal_used, pswap ) )
             exit(2)
          else:
            print("WARNING - UsedMemory: {0:.2f} -- UsedSwap: {1:.2f}".format( ptotal_used, pswap ) )
            exit(1)
     elif ptotal_used >= args.warning:
          print("WARNING - UsedMemory: {0:.2f} -- UsedSwap: {1:.2f}".format( ptotal_used, pswap ) )
          exit(1)
     else:
         print("OK - UsedMemory: {0:.2f} -- UsedSwap: {1:.2f}".format( ptotal_used, pswap ) )
         exit(0)


