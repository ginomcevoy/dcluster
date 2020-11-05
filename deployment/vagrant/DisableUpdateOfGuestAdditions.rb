# No need for guest additions for now, this disables any
# attempt at downloading guest additions from internet
# 
# NOTE: This configuration requires vagrant-vbguest gem
# gem install vagrant-vbguest

Vagrant.configure('2') do |config|
  config.vbguest.auto_update = false  
end
