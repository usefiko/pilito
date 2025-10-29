"""
Debug command to check when node tag configuration
Usage: python manage.py debug_when_node_tags [workflow_id]
"""

from django.core.management.base import BaseCommand
from workflow.models import WhenNode, Workflow
from message.models import Customer
from colorama import Fore, Style, init

init(autoreset=True)


class Command(BaseCommand):
    help = 'Debug when node tag configuration to diagnose tag filtering issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workflow',
            type=str,
            help='Workflow ID to check (optional, will check all if not provided)'
        )
        parser.add_argument(
            '--when-node',
            type=str,
            help='Specific when node ID to check'
        )

    def handle(self, *args, **options):
        self.stdout.write(f"\n{Fore.CYAN}{'='*80}")
        self.stdout.write(f"{Fore.CYAN}When Node Tag Configuration Debugger")
        self.stdout.write(f"{Fore.CYAN}{'='*80}\n")

        if options['when_node']:
            # Check specific when node
            try:
                when_node = WhenNode.objects.get(id=options['when_node'])
                self.check_when_node(when_node)
            except WhenNode.DoesNotExist:
                self.stdout.write(f"{Fore.RED}❌ When node not found: {options['when_node']}\n")
                return

        elif options['workflow']:
            # Check all when nodes in a workflow
            try:
                workflow = Workflow.objects.get(id=options['workflow'])
                self.stdout.write(f"{Fore.BLUE}📋 Workflow: {workflow.name}\n")
                
                when_nodes = WhenNode.objects.filter(workflow=workflow)
                if not when_nodes.exists():
                    self.stdout.write(f"{Fore.YELLOW}⚠️  No when nodes found in this workflow\n")
                    return
                
                for when_node in when_nodes:
                    self.check_when_node(when_node)
                    self.stdout.write("\n")
                    
            except Workflow.DoesNotExist:
                self.stdout.write(f"{Fore.RED}❌ Workflow not found: {options['workflow']}\n")
                return
        else:
            # Check all when nodes with receive_message type that have tags
            self.stdout.write(f"{Fore.BLUE}Checking all receive_message when nodes with tags configured...\n\n")
            
            when_nodes = WhenNode.objects.filter(when_type='receive_message').exclude(tags=[])
            
            if not when_nodes.exists():
                self.stdout.write(f"{Fore.YELLOW}⚠️  No receive_message when nodes with tags found\n")
                return
            
            self.stdout.write(f"{Fore.GREEN}Found {when_nodes.count()} when node(s) with tag filtering\n\n")
            
            for when_node in when_nodes:
                self.check_when_node(when_node)
                self.stdout.write("\n")

    def check_when_node(self, when_node):
        """Check a single when node configuration"""
        self.stdout.write(f"{Fore.CYAN}{'─'*80}")
        self.stdout.write(f"{Fore.CYAN}📍 When Node: {when_node.title}")
        self.stdout.write(f"{Fore.CYAN}{'─'*80}")
        
        self.stdout.write(f"   ID: {when_node.id}")
        self.stdout.write(f"   Workflow: {when_node.workflow.name}")
        self.stdout.write(f"   Type: {when_node.when_type}")
        self.stdout.write(f"   Active: {when_node.workflow.is_active()}")
        
        # Check tag configuration
        self.stdout.write(f"\n{Fore.YELLOW}🏷️  Tag Configuration:")
        
        if when_node.tags:
            if isinstance(when_node.tags, list):
                if len(when_node.tags) > 0:
                    self.stdout.write(f"{Fore.GREEN}   ✅ Tags configured: {when_node.tags}")
                    self.stdout.write(f"   📊 Number of tags: {len(when_node.tags)}")
                    self.stdout.write(f"   📝 Tag type: {type(when_node.tags)}")
                    
                    # Show normalized tags
                    normalized = [str(tag).lower().strip() for tag in when_node.tags if tag]
                    self.stdout.write(f"   🔄 Normalized tags: {normalized}")
                else:
                    self.stdout.write(f"{Fore.RED}   ❌ Tags field is an empty list")
                    self.stdout.write(f"{Fore.YELLOW}   ⚠️  This when node will match ALL messages (no tag filtering)")
            else:
                self.stdout.write(f"{Fore.RED}   ❌ Tags field is not a list: {type(when_node.tags)}")
                self.stdout.write(f"   Value: {when_node.tags}")
        else:
            self.stdout.write(f"{Fore.RED}   ❌ No tags configured (tags field is empty/None)")
            self.stdout.write(f"{Fore.YELLOW}   ⚠️  This when node will match ALL messages (no tag filtering)")
        
        # Check other filters
        self.stdout.write(f"\n{Fore.YELLOW}🔍 Other Filters:")
        
        if when_node.keywords:
            self.stdout.write(f"   Keywords: {when_node.keywords}")
        else:
            self.stdout.write(f"   Keywords: Not configured")
        
        if when_node.channels:
            self.stdout.write(f"   Channels: {when_node.channels}")
        else:
            self.stdout.write(f"   Channels: Not configured (all channels)")
        
        # Show matching logic
        self.stdout.write(f"\n{Fore.YELLOW}📋 Matching Logic:")
        
        conditions = []
        if when_node.keywords:
            conditions.append(f"Message contains keywords: {when_node.keywords}")
        if when_node.channels and 'all' not in when_node.channels:
            conditions.append(f"Message from channel: {when_node.channels}")
        if when_node.tags and len(when_node.tags) > 0:
            conditions.append(f"Customer has tag: {when_node.tags}")
        
        if conditions:
            self.stdout.write(f"   This when node will trigger when:")
            for i, condition in enumerate(conditions, 1):
                self.stdout.write(f"   {i}. {condition}")
            self.stdout.write(f"   {Fore.CYAN}(All conditions must be met)")
        else:
            self.stdout.write(f"{Fore.YELLOW}   ⚠️  No filters configured - will match ALL messages!")
        
        # Check for customers with matching tags
        if when_node.tags and len(when_node.tags) > 0:
            self.stdout.write(f"\n{Fore.YELLOW}👥 Customers with Matching Tags:")
            
            normalized_when_tags = [str(tag).lower().strip() for tag in when_node.tags if tag]
            
            # Find customers with any of the required tags
            from django.db.models import Q
            query = Q()
            for tag_name in when_node.tags:
                query |= Q(tag__name__iexact=tag_name)
            
            matching_customers = Customer.objects.filter(query).distinct()
            
            if matching_customers.exists():
                self.stdout.write(f"{Fore.GREEN}   ✅ Found {matching_customers.count()} customer(s) with matching tags:")
                for customer in matching_customers[:5]:  # Show first 5
                    customer_tags = list(customer.tag.values_list('name', flat=True))
                    normalized_customer_tags = [str(tag).lower().strip() for tag in customer_tags if tag]
                    matching = set(normalized_when_tags) & set(normalized_customer_tags)
                    self.stdout.write(f"      • {customer} - Tags: {customer_tags} (Matching: {list(matching)})")
                
                if matching_customers.count() > 5:
                    self.stdout.write(f"      ... and {matching_customers.count() - 5} more")
            else:
                self.stdout.write(f"{Fore.YELLOW}   ⚠️  No customers found with matching tags")
                self.stdout.write(f"   💡 Make sure customers are tagged with one of: {when_node.tags}")

        # Recommendations
        self.stdout.write(f"\n{Fore.YELLOW}💡 Recommendations:")
        
        if not when_node.tags or len(when_node.tags) == 0:
            self.stdout.write(f"{Fore.RED}   ⚠️  No tag filtering configured!")
            self.stdout.write(f"   To fix:")
            self.stdout.write(f"   1. Edit this when node in the UI")
            self.stdout.write(f"   2. Add tag(s) you want to filter by")
            self.stdout.write(f"   3. Save the when node")
        elif not when_node.workflow.is_active():
            self.stdout.write(f"{Fore.YELLOW}   ⚠️  Workflow is not active")
            self.stdout.write(f"   To fix: Activate the workflow in the UI")
        else:
            self.stdout.write(f"{Fore.GREEN}   ✅ Configuration looks correct!")
            self.stdout.write(f"   Tags are properly configured for filtering")

