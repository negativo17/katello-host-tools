%global dnf_install (0%{?rhel} >= 8) || 0%{?fedora}
%global yum_install (0%{?rhel} == 7)

%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%if %{dnf_install}
%global katello_libdir  %{python3_sitelib}/katello
%global plugins_dir     %{python3_sitelib}/dnf-plugins
%global plugins_confdir %{_sysconfdir}/dnf/plugins
%else
%global katello_libdir  %{python2_sitelib}/katello
%global plugins_dir     %{_prefix}/lib/yum-plugins
%global plugins_confdir %{_sysconfdir}/yum/pluginconf.d
%endif

Name:       katello-host-tools
Version:    3.5.4
Release:    3%{?dist}
Summary:    A set of commands and yum plugins that support a Katello host
License:    LGPLv2
URL:        https://github.com/Katello/%{name}
BuildArch:  noarch

Source0:    https://codeload.github.com/Katello/%{name}/tar.gz/%{version}#/%{name}-%{version}.tar.gz

Requires:   crontabs
Requires:   subscription-manager

%if %{dnf_install}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       python3-subscription-manager-rhsm
Obsoletes:      %{name}-fact-plugin < %{version}-%{release}
%else
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:       python-rhsm
Requires:       %{name}-fact-plugin == %{version}-%{release}
%endif

%description
A set of commands and yum plugins that support a Katello host including faster
package profile uploading and bound repository reporting. This is required for
errata and package applicability reporting.

%if %{yum_install}
%package fact-plugin
Summary:    Adds an fqdn fact plugin for subscription-manager
Requires:   subscription-manager
Obsoletes:  katello-agent-fact-plugin <= 3.0.0

%description fact-plugin
A subscription-manager plugin to add an additional fact 'network.fqdn' if not
present.
%endif

%package tracer
BuildArch:  noarch
Summary:    Adds Tracer functionality to a client managed by katello-host-tools
Requires: %{name} = %{version}-%{release}
%if %{dnf_install}
Requires: python3-tracer
%endif

%description tracer
Adds Tracer functionality to a client managed by katello-host-tools

%prep
%autosetup -p1

%build
pushd src
%if %{dnf_install}
%{__python3} setup.py build
%else
%{__python} setup.py build
%endif
popd

%install
mkdir -p %{buildroot}%{katello_libdir}
mkdir -p %{buildroot}%{plugins_dir}
mkdir -p %{buildroot}%{plugins_confdir}

cp src/katello/*.py %{buildroot}%{katello_libdir}/

# YUM/DNF plugin
%if %{dnf_install}
cp etc/yum/pluginconf.d/tracer_upload.conf %{buildroot}%{plugins_confdir}/
cp src/dnf_plugins/*.py %{buildroot}%{plugins_dir}/
rm %{buildroot}%{plugins_dir}/__init__.py
%else
cp etc/yum/pluginconf.d/*.conf %{buildroot}%{plugins_confdir}/
cp src/yum-plugins/*.py %{buildroot}%{plugins_dir}/
%endif

# Executables
mkdir -p %{buildroot}%{_sbindir}
%if %{dnf_install}
cp extra/katello-tracer-upload-dnf %{buildroot}%{_sbindir}/katello-tracer-upload
%else
cp bin/* %{buildroot}%{_sbindir}/
%endif

# RHSM plugin
%if %{yum_install}
mkdir -p %{buildroot}%{_sysconfdir}/rhsm/pluginconf.d/
mkdir -p %{buildroot}%{_datadir}/rhsm-plugins/
cp etc/rhsm/pluginconf.d/fqdn.FactsPlugin.conf %{buildroot}%{_sysconfdir}/rhsm/pluginconf.d/fqdn.FactsPlugin.conf
cp src/rhsm-plugins/fqdn.py %{buildroot}%{_datadir}/rhsm-plugins/fqdn.py
%endif

# Cache directory
mkdir -p %{buildroot}%{_localstatedir}/cache/katello-agent/

# crontab
mkdir -p %{buildroot}%{_sysconfdir}/cron.d/
cp extra/katello-agent-send.cron %{buildroot}%{_sysconfdir}/cron.d/%{name}

%posttrans
katello-package-upload 2> /dev/null
katello-enabled-repos-upload 2> /dev/null
exit 0

%files
%license LICENSE
%dir %{_localstatedir}/cache/katello-agent/
%dir %{katello_libdir}/
%{katello_libdir}/constants.py*
%{katello_libdir}/enabled_report.py*
%{katello_libdir}/packages.py*
%{katello_libdir}/repos.py*
%{katello_libdir}/uep.py*
%{katello_libdir}/utils.py*
%{katello_libdir}/__init__.py*
%config(noreplace) %attr(0644, root, root) %{_sysconfdir}/cron.d/%{name}

%if %{dnf_install}
%dir %{katello_libdir}/__pycache__/
%{katello_libdir}/__pycache__/constants.*
%{katello_libdir}/__pycache__/enabled_report.*
%{katello_libdir}/__pycache__/packages.*
%{katello_libdir}/__pycache__/repos.*
%{katello_libdir}/__pycache__/uep.*
%{katello_libdir}/__pycache__/utils.*
%{katello_libdir}/__pycache__/__init__.*
%else
%config(noreplace) %{plugins_confdir}/package_upload.conf
%config(noreplace) %{plugins_confdir}/enabled_repos_upload.conf
%attr(750, root, root) %{_sbindir}/katello-package-upload
%attr(750, root, root) %{_sbindir}/katello-enabled-repos-upload
%{plugins_dir}/enabled_repos_upload.py*
%{plugins_dir}/package_upload.py*
%endif

%if %{yum_install}
%files fact-plugin
%dir %{_sysconfdir}/rhsm/
%dir %{_sysconfdir}/rhsm/pluginconf.d/
%config %{_sysconfdir}/rhsm/pluginconf.d/fqdn.FactsPlugin.conf
%dir %{_datadir}/rhsm-plugins/
%{_datadir}/rhsm-plugins/fqdn.*
%endif

%files tracer
%{plugins_dir}/tracer_upload.py*
%{katello_libdir}/tracer.py*
%{plugins_confdir}/tracer_upload.conf
%attr(750, root, root) %{_sbindir}/katello-tracer-upload

%if %{dnf_install}
%{katello_libdir}/__pycache__/tracer.*
%{plugins_dir}/__pycache__/tracer_upload.*
%endif

%changelog
* Thu Apr 22 2021 Simone Caronni <negativo17@gmail.com> - 3.5.4-3
- Fix URLs.

* Mon Dec 07 2020 Simone Caronni <negativo17@gmail.com> - 3.5.4-2
- Update SPEC file for Fedora 33.
- Clean up SPEC file, drop SUSE and CentOS/RHEL 6 support.
- Drop support for agent on Fedora.
- Trim changelog.

* Wed May 27 2020 Jonathon Turel - 3.5.4-1
- Release 3.5.4

* Fri Mar 27 2020 Bernhard Suttner - 3.5.3-3
- SLES requires python2-zypp-plugin

* Mon Mar 23 2020 Jonathon Turel - 3.5.3-2
- require matching katello-host-tools version in subpackages

* Mon Feb 17 2020 Jonathon Turel - 3.5.3-1
- Release 3.5.3

* Tue Jan 14 2020 Evgeni Golov - 3.5.2-2
- Rebuild for EL8 client repository

* Mon Jan 13 2020 Jonathon Turel - 3.5.2-1
- Release 3.5.2

* Thu Aug 1 2019 Jonathon Turel - 3.5.1-2
- Updates from SLES builds

* Fri Jun 21 2019 Jonathon Turel - 3.5.1-1
- Fixes #26920 - Install errata via libdnf
- Fixes #26375 - zypper plugin for tracer upload

* Thu May 23 2019 Garret Rumohr - 3.5.0-4
- Fixes #26837 - Corrects string replacement in /etc/sysconfig/goferd by RPM script

* Thu May 23 2019 Evgeni Golov - 3.5.0-3
- don't build the tracer plugin on RHEL < 7

* Tue Apr 23 2019 Evgeni Golov - 3.5.0-2
- Don't ship fact-plugin on modern Fedora and EL

* Thu Mar 28 2019 Justin Sherrill - 3.5.0-1
- Update to 3.5.0, drop support for agent on f27 and f28
- Install katello-tracer-upload wrapper on DNF platforms

* Wed Jan 30 2019 Evgeni Golov - 3.4.2-2
- Explicitly build using Python3 on Python3 distibutions

* Mon Jan 14 2019 Jonathon Turel <jturel@gmail.com> - 3.4.2-1
- Fixes #25725 - disable plugins if we have subman profiles
