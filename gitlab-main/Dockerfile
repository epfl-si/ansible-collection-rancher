ARG GITLAB_CE_BASE_VERSION
FROM gitlab/gitlab-ce:$GITLAB_CE_BASE_VERSION
MAINTAINER EPFL Gitlab admins <gitlab-admins@groupes.epfl.ch>

# node is a hidden dependency of "bundle exec rake db:migrate RAILS_ENV=production"
# The rest are debugging tools
RUN apt -qy update && apt -qy install nodejs iproute2 iputils-ping netcat-openbsd libssh2-1 openssh-server

# This may not be the smartest way of achieving this, but it does get
# omniauth-tequila to install, and therefore load, along with all the others:
RUN ln -s . /opt/gitlab/embedded/lib/ruby/gems/3.1.0/bundler
RUN echo "gem 'omniauth-tequila', :git => 'https://github.com/domq/omniauth-tequila.git' " >> /opt/gitlab/embedded/service/gitlab-rails/Gemfile
RUN cd /opt/gitlab/embedded/service/gitlab-rails && bundle config unset frozen && bundle install

# Fix to https://gitlab.com/epfl-isasfsd/gitlab-docker/-/issues/9
RUN set -e -x; \
     cd /opt/gitlab/embedded/service/gitlab-rails; \
     curl https://gitlab.com/epfl-isasfsd/gitlab-foss/-/merge_requests/1.diff | git apply

# To check that omniauth-tequila was indeed installed in the correct place:
# docker run --rm -it <image_hash> ls /opt/gitlab/embedded/lib/ruby/gems/2.5.0/gems/

# HEALTHCHECK --start-period=600s CMD /opt/gitlab/bin/gitlab-healthcheck --fail
