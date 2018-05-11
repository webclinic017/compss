package es.bsc.compss.nio.utils;

import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Semaphore;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import es.bsc.comm.Connection;
import es.bsc.comm.nio.NIOConnection;
import es.bsc.comm.stage.Transfer;
import es.bsc.compss.log.Loggers;
import es.bsc.compss.nio.NIOAgent;
import es.bsc.compss.util.BindingDataManager;

public class NIOBindingDataManager extends BindingDataManager{
    
    protected static final Logger LOGGER = LogManager.getLogger(Loggers.COMM);
    private static final boolean DEBUG = LOGGER.isDebugEnabled();
    
    private static Map<NIOConnection, NIOBindingObjectTransferListener> listeners = new ConcurrentHashMap<NIOConnection, NIOBindingObjectTransferListener>();
    
    static {
        System.loadLibrary("bindings_common");
    }
    
    public native static int sendNativeObject(String id, NIOBindingObjectStream nioStrm);
    
    public native static int receiveNativeObject(String id, int type, NIOBindingObjectStream nioStream);

    public static void receiveBindingObject(NIOAgent agent, NIOConnection c, String sourceId, int type) {
        Semaphore sem = new Semaphore(0);
        NIOBindingObjectTransferListener nbol = new NIOBindingObjectTransferListener(agent, sem);
        synchronized (listeners) {
            listeners.put(c, nbol);
        }
        NIOBindingObjectStream nbos = new NIOBindingObjectStream((NIOConnection)c, nbol);
        NIOBindingObjectReceiver receiver = new NIOBindingObjectReceiver(c, sourceId, type, nbos);
        Thread t = new Thread(receiver);
        t.setName("BindingObjectReceiver_" + sourceId);
        t.start();

    }

    public static void receivedPartialBindingObject(NIOConnection c, Transfer t) {
        NIOBindingObjectTransferListener nbol = listeners.get(c);
        nbol.setTransfer(t);
        nbol.notifyEnd();
    }

    public static void objectReceived(NIOConnection c) {
        NIOBindingObjectTransferListener nbol = listeners.remove(c);
        nbol.getAgent().receivedData(c, nbol.getTransfer());
    }
    
    
   
}
