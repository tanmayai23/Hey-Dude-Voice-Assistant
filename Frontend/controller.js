// Hey Dude — Settings, profile, commands and contacts management
$(document).ready(function () {
  // Legacy hooks still exposed for backward compatibility with backend
  function DisplayMessage(message) {
    $("#SiriMessage").text(message || "");
  }
  function ShowHood() {
    $("#LiveBar").attr("hidden", true);
  }
  if (typeof eel !== "undefined" && eel.expose) {
    eel.expose(DisplayMessage, "DisplayMessage");
    eel.expose(ShowHood, "ShowHood");
  }

  // ===== PROFILE MANAGEMENT =====
  
  // Load profile data on page load
  function loadProfileData() {
    if (typeof eel !== 'undefined' && typeof eel.get_profile === 'function') {
      eel.get_profile()(function(profile) {
        if (profile) {
          $('#OwnerName').text(profile.name || 'Not set');
          $('#MobileNo').text(profile.mobile || 'Not set');
          $('#Email').text(profile.email || 'Not set');
          $('#City').text(profile.city || 'Not set');
          
          // Pre-fill edit form
          $('#InputOwnerName').val(profile.name || '');
          $('#InputMobileNo').val(profile.mobile || '');
          $('#InputEmail').val(profile.email || '');
          $('#InputCity').val(profile.city || '');
        }
      });
    }
  }

  // Update profile button
  $('#UpdateBtn').click(function() {
    const name = $('#InputOwnerName').val().trim();
    const mobile = $('#InputMobileNo').val().trim();
    const email = $('#InputEmail').val().trim();
    const city = $('#InputCity').val().trim();

    if (!name) {
      alert('Please enter your name');
      return;
    }

    const profile = { name, mobile, email, city };
    
    if (typeof eel !== 'undefined' && typeof eel.update_profile === 'function') {
      eel.update_profile(profile)(function(result) {
        if (result.success) {
          alert('Profile updated successfully!');
          loadProfileData();
        } else {
          alert('Error updating profile: ' + result.error);
        }
      });
    }
  });

  // ===== SYSTEM COMMANDS MANAGEMENT =====
  
  // Load system commands
  function loadSystemCommands() {
    if (typeof eel !== 'undefined' && typeof eel.get_system_commands === 'function') {
      eel.get_system_commands()(function(commands) {
        $('#TableData').empty();
        commands.forEach((cmd, index) => {
          $('#TableData').append(`
            <tr>
              <td>${index + 1}</td>
              <td>${cmd.name}</td>
              <td>${cmd.path}</td>
              <td><button class="btn btn-sm btn-danger delete-sys-cmd" data-id="${cmd.id}">Delete</button></td>
            </tr>
          `);
        });
      });
    }
  }

  // Add system command
  $('#SysCommandAddBtn').click(function() {
    const keyword = $('#SysCommandKey').val().trim();
    const path = $('#SysCommandValue').val().trim();

    if (!keyword || !path) {
      alert('Please fill both keyword and path');
      return;
    }

    if (typeof eel !== 'undefined' && typeof eel.add_system_command === 'function') {
      eel.add_system_command(keyword, path)(function(result) {
        if (result.success) {
          alert('Command added successfully!');
          $('#SysCommandKey').val('');
          $('#SysCommandValue').val('');
          loadSystemCommands();
        } else {
          alert('Error: ' + result.error);
        }
      });
    }
  });

  // Delete system command
  $(document).on('click', '.delete-sys-cmd', function() {
    const id = $(this).data('id');
    if (confirm('Delete this command?')) {
      if (typeof eel !== 'undefined' && typeof eel.delete_system_command === 'function') {
        eel.delete_system_command(id)(function(result) {
          if (result.success) {
            loadSystemCommands();
          } else {
            alert('Error: ' + result.error);
          }
        });
      }
    }
  });

  // ===== WEB COMMANDS MANAGEMENT =====
  
  // Load web commands
  function loadWebCommands() {
    if (typeof eel !== 'undefined' && typeof eel.get_web_commands === 'function') {
      eel.get_web_commands()(function(commands) {
        $('#WebTableData').empty();
        commands.forEach((cmd, index) => {
          $('#WebTableData').append(`
            <tr>
              <td>${index + 1}</td>
              <td>${cmd.name}</td>
              <td>${cmd.url}</td>
              <td><button class="btn btn-sm btn-danger delete-web-cmd" data-id="${cmd.id}">Delete</button></td>
            </tr>
          `);
        });
      });
    }
  }

  // Add web command
  $('#WebCommandAddBtn').click(function() {
    const keyword = $('#WebCommandKey').val().trim();
    const url = $('#WebCommandValue').val().trim();

    if (!keyword || !url) {
      alert('Please fill both keyword and URL');
      return;
    }

    if (typeof eel !== 'undefined' && typeof eel.add_web_command === 'function') {
      eel.add_web_command(keyword, url)(function(result) {
        if (result.success) {
          alert('Web command added successfully!');
          $('#WebCommandKey').val('');
          $('#WebCommandValue').val('');
          loadWebCommands();
        } else {
          alert('Error: ' + result.error);
        }
      });
    }
  });

  // Delete web command
  $(document).on('click', '.delete-web-cmd', function() {
    const id = $(this).data('id');
    if (confirm('Delete this command?')) {
      if (typeof eel !== 'undefined' && typeof eel.delete_web_command === 'function') {
        eel.delete_web_command(id)(function(result) {
          if (result.success) {
            loadWebCommands();
          } else {
            alert('Error: ' + result.error);
          }
        });
      }
    }
  });

  // ===== CONTACTS MANAGEMENT =====
  
  // Load contacts
  function loadContacts() {
    if (typeof eel !== 'undefined' && typeof eel.get_contacts === 'function') {
      eel.get_contacts()(function(contacts) {
        $('#ContactTableData').empty();
        contacts.forEach((contact, index) => {
          $('#ContactTableData').append(`
            <tr>
              <td>${index + 1}</td>
              <td>${contact.name}</td>
              <td>${contact.mobile}</td>
              <td>${contact.address || '-'}</td>
              <td><button class="btn btn-sm btn-danger delete-contact" data-id="${contact.id}">Delete</button></td>
            </tr>
          `);
        });
      });
    }
  }

  // Add contact
  $('#AddContactBtn').click(function() {
    const name = $('#InputContactName').val().trim();
    const mobile = $('#InputContactMobileNo').val().trim();
    const address = $('#InputContactCity').val().trim();

    if (!name || !mobile) {
      alert('Name and Mobile are required');
      return;
    }

    if (typeof eel !== 'undefined' && typeof eel.add_contact === 'function') {
      eel.add_contact(name, mobile, address)(function(result) {
        if (result.success) {
          alert('Contact added successfully!');
          $('#InputContactName').val('');
          $('#InputContactMobileNo').val('');
          $('#InputContactCity').val('');
          loadContacts();
        } else {
          alert('Error: ' + result.error);
        }
      });
    }
  });

  // Delete contact
  $(document).on('click', '.delete-contact', function() {
    const id = $(this).data('id');
    if (confirm('Delete this contact?')) {
      if (typeof eel !== 'undefined' && typeof eel.delete_contact === 'function') {
        eel.delete_contact(id)(function(result) {
          if (result.success) {
            loadContacts();
          } else {
            alert('Error: ' + result.error);
          }
        });
      }
    }
  });

  // Load all data when modal is opened
  $('#exampleModal').on('shown.bs.modal', function() {
    loadProfileData();
    loadSystemCommands();
    loadWebCommands();
    loadContacts();
  });

  // Initial load
  setTimeout(function() {
    loadProfileData();
  }, 1000);
});
