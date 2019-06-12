/*
 *  Copyright 2002-2019 Barcelona Supercomputing Center (www.bsc.es)
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 */

package es.bsc.compss.executor.external.piped;

import es.bsc.compss.executor.external.ExternalExecutor;
import es.bsc.compss.executor.external.ExternalExecutorException;
import es.bsc.compss.executor.external.commands.ExternalCommand;
import es.bsc.compss.executor.external.piped.commands.AddedExecutorPipeCommand;
import es.bsc.compss.executor.external.piped.commands.AliveReplyPipeCommand;
import es.bsc.compss.executor.external.piped.commands.ChannelCreatedPipeCommand;
import es.bsc.compss.executor.external.piped.commands.EndTaskPipeCommand;
import es.bsc.compss.executor.external.piped.commands.ErrorPipeCommand;
import es.bsc.compss.executor.external.piped.commands.ExecutorPIDReplyPipeCommand;
import es.bsc.compss.executor.external.piped.commands.PipeCommand;
import es.bsc.compss.executor.external.piped.commands.PongPipeCommand;
import es.bsc.compss.executor.external.piped.commands.QuitPipeCommand;
import es.bsc.compss.executor.external.piped.commands.RemovedExecutorPipeCommand;
import es.bsc.compss.executor.external.piped.commands.WorkerStartedPipeCommand;
import es.bsc.compss.executor.external.piped.exceptions.ClosedPipeException;
import es.bsc.compss.executor.external.piped.exceptions.UnknownCommandException;
import es.bsc.compss.log.Loggers;
import es.bsc.compss.util.ErrorManager;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;


public class PipePair implements ExternalExecutor<PipeCommand> {

    private static final Logger LOGGER = LogManager.getLogger(Loggers.WORKER_EXECUTOR);
    // Logger messages
    private static final String ERROR_PIPE_CLOSE = "Error on closing pipe ";
    private static final String WRITE_PIPE_CLOSING_NOT_EXISTS = "Deleted pipe being written blocks the execution";
    private static final String READ_PIPE_CLOSING_NOT_EXISTS = "Deleted pipe read written blocks the execution";

    private static final String CLOSED_PIPE_ERROR = "CLOSED_PIPE_ERROR";

    protected static final String TOKEN_NEW_LINE = "\n";
    protected static final String TOKEN_SEP = " ";

    private static final int MAX_WRITE_PIPE_RETRIES = 3;
    private static final int PIPE_ERROR_WAIT_TIME = 50;
    private static final long PIPE_READ_COMMAND_PERIOD = 20;

    private final String pipePath;

    // Number of threads waiting to write on the pipe
    private BufferedReader reader;
    private final Lock sendMutex = new ReentrantLock();
    private int senders;
    private int readers;
    private boolean closed = false;

    public PipePair(String basePipePath, String id) {
        this.pipePath = basePipePath + id;
    }

    public final String getPipesLocation() {
        return this.pipePath;
    }

    public final String getInboundPipe() {
        return this.pipePath + ".inbound";
    }

    public final String getOutboundPipe() {
        return this.pipePath + ".outbound";
    }

    /**
     * Delete pipe.
     */
    public final void delete() {
        File f = new File(this.pipePath + ".inbound");
        if (f.exists()) {
            f.delete();
        }
        f = new File(this.pipePath + ".outbound");
        if (f.exists()) {
            f.delete();
        }
    }

    @Override
    public boolean sendCommand(PipeCommand command) {
        boolean done = false;
        int retries = 0;
        String taskCMD = command.getAsString();
        String writePipe = this.pipePath + ".outbound";
        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("EXECUTOR COMMAND: " + taskCMD + " @ " + writePipe);
        }
        taskCMD = taskCMD + TOKEN_NEW_LINE;
        while (!done && retries < MAX_WRITE_PIPE_RETRIES) {
            // Send to pipe : task tID command(jobOut jobErr externalCMD) \n
            if (!new File(writePipe).exists()) {
                LOGGER.debug("Warn pipe doesn't exist. Retry");
                ++retries;
            } else {
                OutputStream output = null;
                synchronized (this) {
                    this.senders++;
                }
                this.sendMutex.lock();
                try {
                    output = new FileOutputStream(writePipe, true);
                    output.write(taskCMD.getBytes());
                    output.flush();
                    synchronized (this) {
                        this.senders--;
                        done = !this.closed;
                    }
                    LOGGER.debug("Written " + taskCMD + " into " + writePipe);
                } catch (IOException e) {
                    synchronized (this) {
                        this.senders--;
                    }
                    LOGGER.debug("Error on pipe write. Retry");
                    ++retries;
                } finally {
                    if (output != null) {
                        try {
                            output.close();
                        } catch (Exception e) {
                            ErrorManager.error(ERROR_PIPE_CLOSE + writePipe, e);
                        }
                    }
                    this.sendMutex.unlock();
                }
            }
            if (!done) {
                try {
                    Thread.sleep(PIPE_ERROR_WAIT_TIME);
                } catch (InterruptedException e) {
                    LOGGER.debug("Pipe error wait time for message " + command + " on pipe " + this.getPipesLocation());
                    // No need to catch such exceptions
                }
            }

        }
        if (!done) {
            LOGGER.debug("Failed to send " + command + " on pipe " + this.getPipesLocation());
        }
        return done;
    }

    @Override
    public String toString() {
        return "READ pipe: " + this.pipePath + ".inbound  WRITE pipe:" + this.pipePath + ".outbound";
    }

    @Override
    public PipeCommand readCommand() throws ExternalExecutorException {
        PipeCommand readCommand = null;
        synchronized (this) {
            if (this.closed) {
                throw new ClosedPipeException();
            }
            this.readers++;
        }
        if (this.reader == null) {
            try {
                String readPipe = getInboundPipe();
                FileInputStream input = new FileInputStream(readPipe);// WARN: This call is blocking for NamedPipes
                this.reader = new BufferedReader(new InputStreamReader(input));
            } catch (FileNotFoundException fnfe) {
                throw new ExternalExecutorException(fnfe);
            }
        }
        synchronized (this) {
            this.readers--;
        }

        try {
            String line = null;
            while (line == null || line.length() == 0) {
                if (this.closed) {
                    throw new ClosedPipeException();
                }
                line = this.reader.readLine();
                if (line == null) {
                    try {
                        Thread.sleep(PIPE_READ_COMMAND_PERIOD);
                    } catch (InterruptedException ie) {
                        // Do nothing
                    }
                }
            }
            LOGGER.debug(Thread.currentThread().getName() + " READS -" + line + "-(" + line.length() + ")");
            readCommand = readCommand(line, line.split(" "));

        } catch (IOException ioe) {
            throw new ExternalExecutorException(ioe);
        }

        if (LOGGER.isDebugEnabled()) {
            LOGGER.debug("EXECUTOR COMMAND: " + readCommand + " @ " + getInboundPipe());
        }
        return readCommand;
    }

    private PipeCommand readCommand(String cmd, String[] command) throws ClosedPipeException, UnknownCommandException {
        PipeCommand readCommand = null;
        String commandTypeTag = command[0].toUpperCase();
        if (commandTypeTag.compareTo(CLOSED_PIPE_ERROR) == 0) {
            throw new ClosedPipeException();
        }
        // Process the received tag
        ExternalCommand.CommandType commandType = ExternalCommand.CommandType.valueOf(commandTypeTag);
        switch (commandType) {
            case PONG:
                readCommand = new PongPipeCommand();
                break;
            case WORKER_STARTED:
                readCommand = new WorkerStartedPipeCommand(command);
                break;
            case ALIVE_REPLY:
                readCommand = new AliveReplyPipeCommand(command);
                break;
            case CHANNEL_CREATED:
                readCommand = new ChannelCreatedPipeCommand(command);
                break;
            case REPLY_EXECUTOR_ID:
                readCommand = new ExecutorPIDReplyPipeCommand(command);
                break;

            case ADDED_EXECUTOR:
                readCommand = new AddedExecutorPipeCommand(command);
                break;
            case REMOVED_EXECUTOR:
                readCommand = new RemovedExecutorPipeCommand(command);
                break;
            case QUIT:
                // This quit is received from our proper shutdown, not from bindings. We just end
                LOGGER.debug("Received quit message");
                readCommand = new QuitPipeCommand();
                break;
            case END_TASK:
                if (command.length < 3) {
                    LOGGER.warn("WARN: Skipping endTask line because is malformed");
                    break;
                }
                // Line of the form: "endTask" ID STATUS D paramType1 paramValue1 ... paramTypeD paramValueD
                readCommand = new EndTaskPipeCommand(command);
                LOGGER.debug("Received endTask message: " + readCommand.getAsString());
                break;
            case ERROR:
                String[] expected = Arrays.copyOfRange(command, 1, command.length);
                PipeCommand expectedCommand = readCommand(cmd, expected);
                readCommand = new ErrorPipeCommand(expectedCommand);
                break;
            case PING:
            case EXECUTE_TASK:
            case REMOVE:
            case SERIALIZE:
                // Should not receive any of these tags
            default:
                throw new UnknownCommandException(cmd);
        }
        return readCommand;
    }

    /**
     * Mark Pipe pair as no longer exists.
     */
    public void noLongerExists() {
        int senders;
        int readers;
        synchronized (this) {
            this.closed = true;
            senders = this.senders;
            readers = this.readers;
        }

        String readPipe = this.pipePath + ".outbound";
        while (senders > 0) {
            // Try to read from pipe
            try (FileInputStream input = new FileInputStream(readPipe)) {
                input.read();
            } catch (FileNotFoundException fnfe) {
                ErrorManager.fatal(WRITE_PIPE_CLOSING_NOT_EXISTS, fnfe);
            } catch (IOException ioe) {
                ErrorManager.fatal(WRITE_PIPE_CLOSING_NOT_EXISTS, ioe);
            }

            // Sleep
            try {
                Thread.sleep(50);
            } catch (InterruptedException ie) {
                // No need to catch such exception
            }
            synchronized (this) {
                senders = this.senders;
            }
        }

        String writePipe = this.pipePath + ".inbound";
        if (readers > 0) {
            File pipe = new File(writePipe);
            if (!pipe.exists()) {
                ErrorManager.fatal(READ_PIPE_CLOSING_NOT_EXISTS);
            } else {
                try (FileOutputStream fos = new FileOutputStream(writePipe)) {
                    String message = CLOSED_PIPE_ERROR + "\n";
                    fos.write(message.getBytes());
                    fos.flush();
                } catch (IOException ioe) {
                    ioe.printStackTrace();
                }
            }
        }
        if (this.reader != null) {
            try {
                this.reader.close();
                this.reader = null;
            } catch (IOException ioe) {
                // Already closed. Do nothing
            }
        }
    }

}
