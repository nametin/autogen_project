from util.docker_module import DockerSandbox

sandbox = DockerSandbox()

print("Image:             ", sandbox.image)
print("Network:           ", sandbox.network)
print("Memory limit:      ", sandbox.memory)
print("CPU limit:         ", sandbox.cpus)
print("Volume mapping:    ", sandbox.volume_mapping)
print("Run options:       ", sandbox.run_options)
try:
    sandbox.stop()
except:
    pass
sandbox.start()

sandbox.test()

print("hello")
sandbox.stop()
# sandbox.start()

# sandbox.cleanup()

# sandbox.stop()


# C:\Users\AHMET\Desktop\autogen_project\sandbox

# python -c "from docker_module import DockerSandbox; ds=DockerSandbox(); ds.start()"

# docker run --network none --memory 512m --cpus 0.5 \-v C:\Users\AHMET\Desktop\autogen_project\sandbox:rw \ --name sandbox -d python:3.9 tail -f /dev/null

# docker rm -f sandbox
