package integratedtoolkit.types.resources;

import integratedtoolkit.types.COMPSsNode;
import integratedtoolkit.types.COMPSsWorker;
import integratedtoolkit.types.Implementation;
import integratedtoolkit.types.resources.configuration.Configuration;
import integratedtoolkit.util.CoreManager;

import java.util.LinkedList;


public abstract class Worker<T extends WorkerResourceDescription> extends Resource {

    protected final T description;

    // CoreIds that can be executed by this resource
    private LinkedList<Integer> executableCores;
    // Implementations that can be executed by the resource
    private LinkedList<Implementation<?>>[] executableImpls;
    // ImplIds per core that can be executed by this resource
    private int[][] implSimultaneousTasks;

    // Number of tasks that can be run simultaneously per core id
    private int[] coreSimultaneousTasks;
    // Number of tasks that can be run simultaneously per core id (maxTaskCount not considered)
    private int[] idealSimultaneousTasks;

    
    public Worker(String name, T description, COMPSsNode worker) {
        super(worker);
        int coreCount = CoreManager.getCoreCount();
        this.coreSimultaneousTasks = new int[coreCount];
        this.idealSimultaneousTasks = new int[coreCount];
        this.executableCores = new LinkedList<Integer>();
        this.implSimultaneousTasks = new int[coreCount][];
        this.executableImpls = new LinkedList[coreCount];
        for (int coreId = 0; coreId < coreCount; ++coreId) {
            executableImpls[coreId] = new LinkedList<Implementation<?>>();
            implSimultaneousTasks[coreId] = new int[CoreManager.getCoreImplementations(coreId).length];
        }

        this.description = description;
    }

    public Worker(String name, T description, Configuration config) throws Exception {
        super(name, config);
        int coreCount = CoreManager.getCoreCount();
        this.coreSimultaneousTasks = new int[coreCount];
        this.idealSimultaneousTasks = new int[coreCount];
        this.executableCores = new LinkedList<Integer>();
        this.implSimultaneousTasks = new int[coreCount][];
        this.executableImpls = new LinkedList[coreCount];
        for (int coreId = 0; coreId < coreCount; ++coreId) {
            executableImpls[coreId] = new LinkedList<Implementation<?>>();
            implSimultaneousTasks[coreId] = new int[CoreManager.getCoreImplementations(coreId).length];
        }

        this.description = description;
    }

    public Worker(Worker<T> w) {
        super(w);
        this.coreSimultaneousTasks = w.coreSimultaneousTasks;
        this.idealSimultaneousTasks = w.idealSimultaneousTasks;
        this.executableCores = w.executableCores;
        this.implSimultaneousTasks = w.implSimultaneousTasks;
        this.executableImpls = w.executableImpls;
        this.description = w.description;
    }

    public T getDescription() {
        return description;
    }

    public int getMaxTaskCount() {
        return this.description.getMaxTaskSlots();
    }
    
    public int getUsedTaskCount() {
        return this.description.getUsedTaskSlots();
    }
    
    private void decreaseUsedTaskCount() {
        this.description.setUsedTaskSlots(this.description.getUsedTaskSlots() - 1);
    }
    
    private void increaseUsedTaskCount() {
        this.description.setUsedTaskSlots(this.description.getUsedTaskSlots() + 1);
    }

    /*-------------------------------------------------------------------------
     * ************************************************************************
     * ************************************************************************
     * ********* EXECUTABLE CORES AND IMPLEMENTATIONS MANAGEMENT **************
     * ************************************************************************
     * ************************************************************************
     * -----------------------------------------------------------------------*/
    public void updatedCoreElements(LinkedList<Integer> updatedCoreIds) {
        int coreCount = CoreManager.getCoreCount();
        boolean[] coresToUpdate = new boolean[coreCount];
        for (int coreId : updatedCoreIds) {
            coresToUpdate[coreId] = true;
        }
        boolean[] wasExecutable = new boolean[coreCount];
        for (int coreId : this.executableCores) {
            wasExecutable[coreId] = true;
        }
        this.executableCores.clear();
        LinkedList<Implementation<?>>[] executableImpls = new LinkedList[coreCount];
        int[][] implSimultaneousTasks = new int[coreCount][];
        int[] coreSimultaneousTasks = new int[coreCount];
        int[] idealSimultaneousTasks = new int[coreCount];

        for (int coreId = 0; coreId < coreCount; coreId++) {
            if (!coresToUpdate[coreId]) {
                executableImpls[coreId] = this.executableImpls[coreId];
                implSimultaneousTasks[coreId] = this.implSimultaneousTasks[coreId];
                coreSimultaneousTasks[coreId] = this.coreSimultaneousTasks[coreId];
                idealSimultaneousTasks[coreId] = this.idealSimultaneousTasks[coreId];
                if (wasExecutable[coreId]) {
                    executableCores.add(coreId);
                }
            } else {
                boolean executableCore = false;
                Implementation<?>[] impls = CoreManager.getCoreImplementations(coreId);
                implSimultaneousTasks[coreId] = new int[impls.length];
                executableImpls[coreId] = new LinkedList<Implementation<?>>();
                for (Implementation<?> impl : impls) {
                    if (canRun(impl)) {
                    	int simultaneousCapacity = simultaneousCapacity(impl);
                        idealSimultaneousTasks[coreId] = Math.max(idealSimultaneousTasks[coreId], simultaneousCapacity);
                        implSimultaneousTasks[coreId][impl.getImplementationId()] = simultaneousCapacity;
                        if (implSimultaneousTasks[coreId][impl.getImplementationId()] > 0) {
                            executableImpls[coreId].add(impl);
                            executableCore = true;
                        }
                    }
                }
                if (executableCore) {
                    executableCores.add(coreId);
                }
            }
        }

        this.executableImpls = executableImpls;
        this.implSimultaneousTasks = implSimultaneousTasks;
        this.coreSimultaneousTasks = coreSimultaneousTasks;
        this.idealSimultaneousTasks = idealSimultaneousTasks;
    }

    public void updatedFeatures() {
        int coreCount = CoreManager.getCoreCount();
        executableCores.clear();
        executableImpls = new LinkedList[coreCount];
        implSimultaneousTasks = new int[coreCount][];
        coreSimultaneousTasks = new int[coreCount];
        idealSimultaneousTasks = new int[coreCount];
        for (int coreId = 0; coreId < coreCount; coreId++) {
            boolean executableCore = false;
            Implementation<?>[] impls = CoreManager.getCoreImplementations(coreId);
            implSimultaneousTasks[coreId] = new int[impls.length];
            executableImpls[coreId] = new LinkedList<Implementation<?>>();
            for (Implementation<?> impl : impls) {
                if (canRun(impl)) {
                    int simultaneousCapacity = simultaneousCapacity(impl);
                    idealSimultaneousTasks[coreId] = Math.max(idealSimultaneousTasks[coreId], simultaneousCapacity);
                    implSimultaneousTasks[coreId][impl.getImplementationId()] = simultaneousCapacity;
                    if (simultaneousCapacity > 0) {
                        executableImpls[coreId].add(impl);
                        executableCore = true;
                    }
                }
            }
            if (executableCore) {
                coreSimultaneousTasks[coreId] = Math.min(this.getMaxTaskCount(), idealSimultaneousTasks[coreId]);
                executableCores.add(coreId);
            }
        }
    }

    public LinkedList<Integer> getExecutableCores() {
        return executableCores;
    }

    public LinkedList<Implementation<?>>[] getExecutableImpls() {
        return executableImpls;
    }

    public LinkedList<Implementation<?>> getExecutableImpls(int coreId) {
        return executableImpls[coreId];
    }

    public int[] getIdealSimultaneousTasks() {
        return this.idealSimultaneousTasks;
    }

    public int[] getSimultaneousTasks() {
        return coreSimultaneousTasks;
    }

    public Integer simultaneousCapacity(Implementation<?> impl) {
        return Math.min(fitCount(impl), this.getMaxTaskCount());
    }

    public String getResourceLinks(String prefix) {
        StringBuilder sb = new StringBuilder();
        sb.append(prefix).append("NAME = ").append(getName()).append("\n");
        sb.append(prefix).append("EXEC_CORES = ").append(executableCores).append("\n");
        sb.append(prefix).append("CORE_SIMTASKS = [").append("\n");
        for (int i = 0; i < coreSimultaneousTasks.length; ++i) {
            sb.append(prefix).append("\t").append("CORE = [").append("\n");
            sb.append(prefix).append("\t").append("\t").append("COREID = ").append(i).append("\n");
            sb.append(prefix).append("\t").append("\t").append("SIM_TASKS = ").append(coreSimultaneousTasks[i]).append("\n");
            sb.append(prefix).append("\t").append("]").append("\n");
        }
        sb.append(prefix).append("]").append("\n");
        sb.append(prefix).append("IMPL_SIMTASKS = [").append("\n");
        for (int i = 0; i < implSimultaneousTasks.length; ++i) {
            for (int j = 0; j < implSimultaneousTasks[i].length; ++j) {
                sb.append(prefix).append("\t").append("IMPLEMENTATION = [").append("\n");
                sb.append(prefix).append("\t").append("\t").append("COREID = ").append(i).append("\n");
                sb.append(prefix).append("\t").append("\t").append("IMPLID = ").append(j).append("\n");
                sb.append(prefix).append("\t").append("\t").append("SIM_TASKS = ").append(implSimultaneousTasks[i][j]).append("\n");
                sb.append(prefix).append("\t").append("]").append("\n");
            }
        }
        sb.append(prefix).append("]").append("\n");

        return sb.toString();
    }

    /*-------------------------------------------------------------------------
     * ************************************************************************
     * ************************************************************************
     * ********************* AVAILABLE FEATURES MANAGEMENT ********************
     * ************************************************************************
     * ************************************************************************
     * -----------------------------------------------------------------------*/
    public LinkedList<Integer> getRunnableCores() {
        LinkedList<Integer> cores = new LinkedList<Integer>();
        int coreCount = CoreManager.getCoreCount();
        for (int coreId = 0; coreId < coreCount; coreId++) {
            if (!getRunnableImplementations(coreId).isEmpty()) {
                cores.add(coreId);
            }
        }
        return cores;
    }

    public LinkedList<Implementation<?>>[] getRunnableImplementations() {
        int coreCount = CoreManager.getCoreCount();
        LinkedList<Implementation<?>>[] runnable = new LinkedList[coreCount];
        for (int coreId = 0; coreId < coreCount; coreId++) {
            runnable[coreId] = getRunnableImplementations(coreId);
        }
        return runnable;
    }

    public LinkedList<Implementation<?>> getRunnableImplementations(int coreId) {
        LinkedList<Implementation<?>> runnable = new LinkedList<Implementation<?>>();
        for (Implementation<?> impl : this.executableImpls[coreId]) {
            if (canRunNow((T) impl.getRequirements())) {
                runnable.add(impl);
            }
        }
        return runnable;
    }

    public boolean canRun(int coreId) {
        return this.idealSimultaneousTasks[coreId] > 0;
    }

    public LinkedList<Implementation<?>> canRunNow(LinkedList<Implementation<?>> candidates) {
        LinkedList<Implementation<?>> runnable = new LinkedList<Implementation<?>>();
        for (Implementation<?> impl : candidates) {
            if (canRunNow((T) impl.getRequirements())) {
                runnable.add(impl);
            }
        }
        return runnable;
    }

    public boolean canRunNow(T consumption) {
        return this.getUsedTaskCount() < this.getMaxTaskCount() && this.hasAvailable(consumption);
    }

    public void endTask(T consumption) {
        logger.debug("End task received. Releasing resource." + consumption.getClass().toString());
        this.decreaseUsedTaskCount();
        releaseResource(consumption);
    }

    public boolean runTask(T consumption) {
        if (reserveResource(consumption)) {
            this.increaseUsedTaskCount();
            return true;
        } else {
            return false;
        }
    }

    public abstract String getMonitoringData(String prefix);

    public abstract boolean canRun(Implementation<?> implementation);

    //Internal private methods depending on the resourceType
    public abstract Integer fitCount(Implementation<?> impl);

    public abstract boolean hasAvailable(T consumption);

    public abstract boolean reserveResource(T consumption);

    public abstract void releaseResource(T consumption);

    public void announceCreation() throws Exception {
        COMPSsWorker w = (COMPSsWorker) this.getNode();
        w.announceCreation();
    }

    public void announceDestruction() throws Exception {
        COMPSsWorker w = (COMPSsWorker) this.getNode();
        w.announceDestruction();
    }

    public abstract Worker<?> getSchedulingCopy();
}
